import secrets
import hashlib
import base64
import json
from http import HTTPStatus
from functools import lru_cache
from typing import Dict, Any
from datetime import datetime, timedelta, timezone

import jwt
from jwt import PyJWK, PyJWKClient, InvalidTokenError
from flask_restful import request, abort

from vibe_api.constants import (
    JWT_SECRET,
    JWT_ISSUER,
    PROVIDERS,
    ACCESS_TOKEN_TTL_SEC,
    REFRESH_TOKEN_TTL_SEC,
    InternalErrorCode,
)
from vibe_api.utils.error_handling import make_error_response


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def issue_access_token(sub: int, jkt) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=ACCESS_TOKEN_TTL_SEC)
    payload = {
        "iss": JWT_ISSUER,
        "sub": str(sub),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "cnf": {"jkt": jkt},
    }
    return jwt.encode(
        payload=payload, key=JWT_SECRET, algorithm="HS256", headers={"typ": "JWT"}
    )


def issue_refresh_token(sub: int, ttl_sec: int = REFRESH_TOKEN_TTL_SEC):
    refresh_token = secrets.token_urlsafe(64)
    hashed_refresh_token = hashlib.sha256(refresh_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_sec)
    return hashed_refresh_token, expires_at


@lru_cache(maxsize=16)
def get_jwk_client(jwks_uri: str) -> PyJWKClient:
    return PyJWKClient(jwks_uri)


def verify_id_token_with_jwks(
    provider_key: str, id_token: str, audience: str
) -> Dict[str, Any]:
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
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )
    except InvalidTokenError as e:
        raise ValueError(f"invalid id_token: {e}")

    return claims


def verify_access_token(access_token: str, jkt):
    try:
        claims = jwt.decode(access_token, JWT_SECRET, algorithms=["HS256"])
        if "cnf" not in claims:
            raise ValueError("cnf is not in access token claims")
        jkt_from_access_token = claims["cnf"].get("jkt")
        if jkt_from_access_token is None:
            raise ValueError("jkt is not in access token claims")
        if jkt_from_access_token != jkt:
            raise ValueError("jkt mismatch")
        return claims
    except jwt.ExpiredSignatureError:
        raise ValueError("token expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"invalid token: {e}")


def generate_jkt_from_jwk(jwk: dict) -> str:
    required = None
    if jwk.get("kty") == "EC":
        required = {"kty": "EC", "crv": jwk["crv"], "x": jwk["x"], "y": jwk["y"]}
        canonical = json.dumps(required, separators=(",", ":"), sort_keys=True).encode(
            "utf-8"
        )
    elif jwk.get("kty") == "RSA":
        required = {"kty": "RSA", "e": jwk["e"], "n": jwk["n"]}
        canonical = json.dumps(required, separators=(",", ":"), sort_keys=True).encode(
            "utf-8"
        )
    else:
        raise ValueError("Unsupported kty for thumbprint")
    digest = hashlib.sha256(canonical).digest()
    return b64url(digest)


def verify_dpop(expected_htm: str, expected_htu: str) -> dict:
    dpop_jwt = request.headers.get("DPoP")
    if not dpop_jwt:
        make_error_response(
            int_error_code=InternalErrorCode.NO_AUTHORIZATION,
            message="Missing DPoP proof",
            http_status=HTTPStatus.BAD_REQUEST,
        )

    unverified_header = jwt.get_unverified_header(dpop_jwt)
    jwk = unverified_header.get("jwk")
    if not jwk:
        make_error_response(
            int_error_code=InternalErrorCode.NO_AUTHORIZATION,
            message="DPoP missing JWK in header",
            http_status=HTTPStatus.BAD_REQUEST,
        )

    public_key = PyJWK.from_dict(jwk).key
    claims = jwt.decode(
        jwt=dpop_jwt,
        key=public_key,
        algorithms=[unverified_header.get("alg", "ES256")],
        options={"require": ["iat", "jti"]},
    )

    now = int(datetime.now(timezone.utc).timestamp())
    if claims.get("htm") != expected_htm:
        abort(400, "DPoP htm mismatch")
    if claims.get("htu") != expected_htu:
        abort(400, "DPoP htu mismatch")
    iat = int(claims.get("iat", 0))
    if now < iat:
        make_error_response(
            int_error_code=InternalErrorCode.NO_AUTHORIZATION,
            message="DPoP proof from the future",
            http_status=HTTPStatus.BAD_REQUEST,
        )

    jkt = generate_jkt_from_jwk(jwk)
    return {"claims": claims, "jwk": jwk, "jkt": jkt}


def require_auth(fn):
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("DPoP "):
            return make_error_response(
                int_error_code=InternalErrorCode.NO_AUTHORIZATION,
                message="Use Authorization: DPoP <access_token>",
                http_status=HTTPStatus.UNAUTHORIZED,
            )
        access_token = auth.split(" ", 1)[1]

        dpop = verify_dpop(request.method, request.url)
        jkt = dpop["jkt"]

        try:
            claim = verify_access_token(access_token, jkt)
        except ValueError as e:
            return make_error_response(
                int_error_code=InternalErrorCode.NO_AUTHORIZATION,
                message=str(e),
                http_status=HTTPStatus.UNAUTHORIZED,
            )

        return fn(*args, **kwargs, claim=claim)

    return wrapper
