import os
from functools import lru_cache, wraps
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone

import jwt
from jwt import PyJWKClient, InvalidTokenError
from flask import request

from vibe_api.models.identity import IdentityModel, Provider
from vibe_api.models.user import UserModel, UserStatus
from vibe_api.db import db

JWT_SECRET = os.getenv("JWT_SECRET")
PROVIDERS = {
    "google": {
        "issuer": "https://accounts.google.com",
        "jwks_uri": "https://www.googleapis.com/oauth2/v3/certs",
        "alt_issuers": ["accounts.google.com"],
        "get_name": lambda c: c.get("name"),
        "get_picture": lambda c: c.get("picture"),
        "get_email": lambda c: c.get("email"),
    },
    "apple": {
        "issuer": "https://appleid.apple.com",
        "jwks_uri": "https://appleid.apple.com/auth/keys",
        "alt_issuers": [],
        "get_name": lambda c: c.get("name") or c.get("email"),
        "get_picture": lambda c: None,
        "get_email": lambda c: c.get("email"),
    },
    "naver": {
        "issuer": "https://nid.naver.com",
        "jwks_uri": "https://nid.naver.com/oauth2.0/cert",
        "alt_issuers": [],
        "get_name": lambda c: c.get("name") or c.get("nickname"),
        "get_picture": lambda c: c.get("picture"),
        "get_email": lambda c: c.get("email"),
    },
}

def issue_access_token(sub: int, ttl_sec: int = 900, roles: Optional[list[str]] = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(sub),
        "iat": now,
        "exp": now + timedelta(seconds=ttl_sec),
    }
    if roles:
        payload["roles"] = roles

    return jwt.encode(payload, JWT_SECRET, algorithm="HS256", headers={"typ": "JWT"})

@lru_cache(maxsize=16)
def get_jwk_client(jwks_uri: str) -> PyJWKClient:
    return PyJWKClient(jwks_uri)

def verify_id_token_with_jwks(id_token: str, provider_key: str, audience: str) -> Dict[str, Any]:
    meta = PROVIDERS[provider_key]
    jwk_client = get_jwk_client(meta["jwks_uri"])

    try:
        # 토큰을 signature verification없이 decode해서 header의 kid값을 이용해 JWKS에서 일치하는 JWK를 가져온다
        signing_key = jwk_client.get_signing_key_from_jwt(id_token)

        # JWKS로 부터 받아온 JWK를 이용해 토큰의 signature verification과 decode를 진행해서 payload부분을 가져온다
        valid_issuers = {meta["issuer"], *meta.get("alt_issuers", [])}
        claims = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256", "RS512", "ES256", "ES384"],
            audience=audience,
            issuer=valid_issuers,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]}
            )
    except InvalidTokenError as e:
        raise ValueError(f"invalid id_token: {e}")

    return claims

def verify_access_jwt(token: str):
    try:
        claims = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return claims
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {e}")

def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return {"error": "Missing or invalid Authorization header"}, 401

        token = auth_header.split(" ")[1]
        try:
            claims = verify_access_jwt(token)
        except ValueError as e:
            return {"error": str(e)}, 401

        return fn(*args, **kwargs)

    return wrapper






def get_by_provider_subject(provider: Provider | str, provider_sub: str):
    return IdentityModel.query.filter_by(provider=str(provider), provider_sub=provider_sub).one_or_none()

def link_or_create_user(provider: Provider | str, provider_sub: str, claims: Dict[str, Any]):
    provider = str(provider)

    identity = get_by_provider_subject(provider, provider_sub)
    if identity:
        identity.last_login_at = datetime.now(timezone.utc)
        db.session.commit()
        return identity.user

    new_user = UserModel(
        email=claims.get("email"),
        name=claims.get("name"),
        status=UserStatus.ACTIVE,
    )
    db.session.add(new_user)
    db.session.flush()

    identity = IdentityModel(
        user_id=new_user.id,
        provider=provider,
        provider_sub=provider_sub,
        last_login_at=datetime.now(timezone.utc),
    )
    db.session.add(identity)
    db.session.commit()

    return new_user
