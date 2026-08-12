import asyncio
import pytest
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request

from app.api.v1.endpoints.auth import (
    EMAIL_VERIFICATION_TOKEN,
    _consume_security_token,
    _issue_security_token,
    login,
    verify_mfa,
)
from app.core.security import (
    create_access_token,
    generate_totp_code,
    generate_totp_secret,
    get_current_user,
    get_password_hash,
    verify_totp_code,
)
from app.db.models import Base, Role, User, UserSecurityToken
from app.schemas.user import MfaVerifyRequest, UserResponse


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def seed_user(db):
    role = Role(name="public", description="Public user")
    db.add(role)
    db.flush()
    user = User(
        username="security-user",
        email="security@example.com",
        hashed_password="test-hash",
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_request():
    return Request({
        "type": "http",
        "method": "POST",
        "path": "/api/v1/auth/login",
        "headers": [],
    })


def test_security_tokens_are_hashed_single_use_and_expiring():
    db = make_session()
    user = seed_user(db)
    raw = _issue_security_token(db, user, EMAIL_VERIFICATION_TOKEN)
    db.commit()

    stored = db.query(user.__class__).filter(User.id == user.id).one()
    token_row = db.query(UserSecurityToken).one()
    assert token_row.token_hash != raw
    assert _consume_security_token(db, raw, EMAIL_VERIFICATION_TOKEN).id == stored.id
    db.commit()

    with pytest.raises(HTTPException) as exc_info:
        _consume_security_token(db, raw, EMAIL_VERIFICATION_TOKEN)
    assert exc_info.value.status_code == 400
    db.close()


def test_totp_accepts_current_code_and_rejects_malformed_code():
    secret = generate_totp_secret()
    code = generate_totp_code(secret)
    assert verify_totp_code(secret, code)
    assert not verify_totp_code(secret, "123")
    assert not verify_totp_code(secret, "abcdef")


def test_token_version_revokes_existing_access_tokens():
    db = make_session()
    user = seed_user(db)
    token = create_access_token({"sub": str(user.id), "ver": 0})

    authenticated = asyncio.run(get_current_user(token=token, db=db))
    assert authenticated.id == user.id

    user.token_version = 1
    db.commit()
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_current_user(token=token, db=db))
    assert exc_info.value.status_code == 401
    db.close()


def test_authenticated_user_contract_includes_assigned_role_name():
    db = make_session()
    user = seed_user(db)

    response = UserResponse.model_validate(user)

    assert response.roles == ["public"]
    db.close()


def test_privileged_mfa_login_returns_challenge_and_verification_returns_access_token(monkeypatch):
    db = make_session()
    role = Role(name="admin", description="Administrator")
    db.add(role)
    db.flush()
    secret = generate_totp_secret()
    user = User(
        username="mfa-admin",
        email="mfa-admin@example.com",
        hashed_password=get_password_hash("strong-password"),
        role_id=role.id,
        is_active=True,
        is_verified=True,
        mfa_enabled=True,
        mfa_secret=secret,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    form = OAuth2PasswordRequestForm(username="mfa-admin", password="strong-password")
    result = asyncio.run(login(make_request(), form, db))
    assert result["mfa_required"] is True
    assert result["access_token"] is None

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_current_user(token=result["mfa_challenge_token"], db=db))
    assert exc_info.value.status_code == 401

    verified = asyncio.run(verify_mfa(
        make_request(),
        MfaVerifyRequest(challenge_token=result["mfa_challenge_token"], code=generate_totp_code(secret)),
        db,
    ))
    assert verified["access_token"]
    authenticated = asyncio.run(get_current_user(token=verified["access_token"], db=db))
    assert authenticated.id == user.id
    db.close()
