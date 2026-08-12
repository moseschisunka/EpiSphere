import asyncio
from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.endpoints.alerts import get_alert
from app.api.v1.endpoints.facilities import get_facility, list_facilities
from app.core.dependencies import apply_country_scope, enforce_country_scope
from app.db.models import (
    Alert,
    AlertSeverity,
    AlertStatus,
    Base,
    Case,
    Country,
    Disease,
    Facility,
    FacilityType,
    Role,
    User,
)


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def seed_scoped_user(db):
    role = Role(name="country_data_officer", description="Country data officer")
    zambia = Country(name="Zambia", iso_code="ZMB", iso_code_2="ZM")
    kenya = Country(name="Kenya", iso_code="KEN", iso_code_2="KE")
    disease = Disease(name="Cholera", code="A00")
    db.add_all([role, zambia, kenya, disease])
    db.flush()
    user = User(
        username="zmb-officer",
        email="zmb@example.com",
        hashed_password="test-hash",
        role_id=role.id,
        country_id=zambia.id,
        is_active=True,
    )
    db.add(user)
    db.flush()
    db.add_all([
        Case(country_id=zambia.id, disease_id=disease.id, date=date(2026, 8, 1), daily_cases=7),
        Case(country_id=kenya.id, disease_id=disease.id, date=date(2026, 8, 1), daily_cases=11),
    ])
    db.commit()
    db.refresh(user)
    return user, zambia, kenya


def test_country_scope_filters_queries_and_rejects_cross_country_targets():
    db = make_session()
    user, zambia, kenya = seed_scoped_user(db)

    rows = apply_country_scope(db.query(Case), Case, user).all()
    assert {row.country_id for row in rows} == {zambia.id}

    with pytest.raises(HTTPException) as exc_info:
        enforce_country_scope(user, kenya.id)
    assert exc_info.value.status_code == 403
    db.close()


def test_facility_admin_can_only_list_and_open_assigned_facility():
    db = make_session()
    role = Role(name="facility_admin", description="Facility administrator")
    country = Country(name="Zambia", iso_code="ZMB", iso_code_2="ZM")
    db.add_all([role, country])
    db.flush()
    assigned = Facility(name="Assigned Clinic", type=FacilityType.CLINIC, country_id=country.id)
    other = Facility(name="Other Clinic", type=FacilityType.CLINIC, country_id=country.id)
    db.add_all([assigned, other])
    db.flush()
    user = User(
        username="facility-admin",
        email="facility@example.com",
        hashed_password="test-hash",
        role_id=role.id,
        facility_id=assigned.id,
        country_id=country.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    visible = list_facilities(db=db, current_user=user)
    assert [facility.id for facility in visible] == [assigned.id]

    with pytest.raises(HTTPException) as exc_info:
        get_facility(other.id, db=db, current_user=user)
    assert exc_info.value.status_code == 403
    db.close()


def test_alert_from_another_country_is_not_retrievable():
    db = make_session()
    user, zambia, kenya = seed_scoped_user(db)
    disease = db.query(Disease).one()
    alert = Alert(
        country_id=kenya.id,
        disease_id=disease.id,
        severity=AlertSeverity.HIGH,
        status=AlertStatus.TRIGGERED,
        probability_score=0.9,
        detection_method="cusum",
        explanation="Out-of-scope alert",
    )
    db.add(alert)
    db.commit()

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_alert(alert.id, current_user=user, db=db))
    assert exc_info.value.status_code == 404
    db.close()
