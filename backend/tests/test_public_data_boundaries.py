import asyncio
import io
import zipfile

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.endpoints.locations import (
    get_districts_by_province,
    get_location_hierarchy,
    get_provinces_by_country,
)
from app.api.v1.endpoints.news import get_news_article, list_admin_news_articles, list_news_articles
from app.api.v1.endpoints.news import delete_news_article, update_news_article
from app.api.v1.endpoints.dashboard import get_country_dashboard
from app.api.v1.endpoints.reports import get_report, list_reports
from app.core.config import settings
from app.db.models import AuditAction, AuditLog, Base, Country, Facility, FacilityType, NewsArticle, Region, Report, ReportType, Role, User
from app.schemas.news import NewsArticleCreate
from app.services.data_upload import DataUploadService


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def seed_countries_and_users(db):
    officer_role = Role(name="country_data_officer", description="Country officer")
    admin_role = Role(name="admin", description="Administrator")
    region = Region(name="Southern Africa", code="SAF")
    db.add_all([officer_role, admin_role, region])
    db.flush()
    zambia = Country(name="Zambia", iso_code="ZMB", iso_code_2="ZM", region_id=region.id)
    kenya = Country(name="Kenya", iso_code="KEN", iso_code_2="KE", region_id=region.id)
    db.add_all([zambia, kenya])
    db.flush()
    officer = User(
        username="zambia-officer", email="officer@example.com", hashed_password="test-hash",
        role_id=officer_role.id, country_id=zambia.id, is_active=True,
    )
    admin = User(
        username="admin-user", email="admin@example.com", hashed_password="test-hash",
        role_id=admin_role.id, is_active=True,
    )
    db.add_all([officer, admin])
    db.commit()
    return officer, admin, zambia, kenya


def test_public_news_excludes_drafts_and_admins_can_review_them():
    db = make_session()
    _, admin, _, _ = seed_countries_and_users(db)
    public_article = NewsArticle(title="Public", summary="Public summary", content="Public body", is_public=True)
    draft_article = NewsArticle(title="Draft", summary="Draft summary", content="Draft body", is_public=False)
    db.add_all([public_article, draft_article])
    db.commit()

    assert [article.id for article in list_news_articles(db=db)] == [public_article.id]
    assert [article.id for article in list_admin_news_articles(db=db, current_user=admin)] == [draft_article.id, public_article.id]
    with pytest.raises(HTTPException) as exc_info:
        get_news_article(draft_article.id, db=db)
    assert exc_info.value.status_code == 404
    db.close()


def test_public_locations_only_include_consent_visible_facilities():
    db = make_session()
    _, _, zambia, _ = seed_countries_and_users(db)
    visible = Facility(
        name="Visible Clinic", type=FacilityType.CLINIC, country_id=zambia.id,
        province="Lusaka", district="Lusaka", public_visible=True,
    )
    hidden = Facility(
        name="Hidden Clinic", type=FacilityType.CLINIC, country_id=zambia.id,
        province="Secret", district="Secret", public_visible=False,
    )
    db.add_all([visible, hidden])
    db.commit()

    hierarchy = get_location_hierarchy(country_id=zambia.id, db=db)
    country = hierarchy[0]["countries"][0]
    assert [facility["id"] for facility in country["facilities"]] == [visible.id]
    assert country["provinces"] == ["Lusaka"]
    assert get_provinces_by_country(zambia.id, db)["provinces"] == ["Lusaka"]
    assert get_districts_by_province(zambia.id, "Lusaka", db)["districts"] == ["Lusaka"]
    db.close()


def test_country_officer_cannot_read_other_country_report():
    db = make_session()
    officer, _, zambia, kenya = seed_countries_and_users(db)
    zambia_report = Report(
        title="Zambia report", report_type=ReportType.WEEKLY_BULLETIN, country_id=zambia.id,
        file_format="pdf", generated_by=officer.id,
    )
    kenya_report = Report(
        title="Kenya report", report_type=ReportType.WEEKLY_BULLETIN, country_id=kenya.id,
        file_format="pdf", generated_by=officer.id,
    )
    db.add_all([zambia_report, kenya_report])
    db.commit()

    reports = asyncio.run(list_reports(current_user=officer, db=db))
    assert [report.id for report in reports] == [zambia_report.id]
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_report(kenya_report.id, current_user=officer, db=db))
    assert exc_info.value.status_code == 404
    db.close()


def test_country_officer_cannot_open_another_country_dashboard():
    db = make_session()
    officer, _, _, kenya = seed_countries_and_users(db)
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_country_dashboard(kenya.id, current_user=officer, db=db))
    assert exc_info.value.status_code == 403
    db.close()


def test_news_mutations_write_attributable_audit_records():
    db = make_session()
    _, admin, _, _ = seed_countries_and_users(db)
    article = NewsArticle(title="Before", summary="Summary", content="Body", is_public=False)
    db.add(article)
    db.commit()
    payload = NewsArticleCreate(title="After", summary="Updated", content="Updated body", is_public=True)

    update_news_article(article.id, payload, db=db, current_user=admin)
    update_audit = db.query(AuditLog).filter(AuditLog.action == AuditAction.UPDATE).one()
    assert update_audit.user_id == admin.id
    assert update_audit.details["before"]["title"] == "Before"
    assert update_audit.details["after"]["title"] == "After"

    delete_news_article(article.id, db=db, current_user=admin)
    delete_audit = db.query(AuditLog).filter(AuditLog.action == AuditAction.DELETE).one()
    assert delete_audit.user_id == admin.id
    assert delete_audit.resource_id == article.id
    db.close()


def test_xlsx_archive_expansion_limit_is_enforced(monkeypatch):
    monkeypatch.setattr(settings, "MAX_XLSX_UNCOMPRESSED_SIZE", 10)
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("xl/sharedStrings.xml", "x" * 11)

    with pytest.raises(HTTPException) as exc_info:
        DataUploadService(None)._read_dataframe(payload.getvalue(), "xlsx")
    assert exc_info.value.status_code == 413
