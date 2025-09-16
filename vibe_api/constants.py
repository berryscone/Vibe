import os
import enum


GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
APPLE_CLIENT_ID = os.getenv("APPLE_CLIENT_ID")
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ISSUER = os.getenv("JWT_ISSUER")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE")

ACCESS_TOKEN_TTL_SEC = 15 * 60 * 30  # 15 minutes
REFRESH_TOKEN_TTL_SEC = 60 * 60 * 24 * 30  # 30 days
PROVIDERS = {
    "google": {
        "issuer": "https://accounts.google.com",
        "jwks_uri": "https://www.googleapis.com/oauth2/v3/certs",
        "alt_issuers": ["accounts.google.com"],
        "client_id": GOOGLE_CLIENT_ID,
        "get_name": lambda c: c.get("name"),
        "get_picture": lambda c: c.get("picture"),
        "get_email": lambda c: c.get("email"),
    },
    "apple": {
        "issuer": "https://appleid.apple.com",
        "jwks_uri": "https://appleid.apple.com/auth/keys",
        "alt_issuers": [],
        "client_id": APPLE_CLIENT_ID,
        "get_name": lambda c: c.get("name") or c.get("email"),
        "get_picture": lambda c: None,
        "get_email": lambda c: c.get("email"),
    },
    "naver": {
        "issuer": "https://nid.naver.com",
        "jwks_uri": "https://nid.naver.com/oauth2.0/cert",
        "alt_issuers": [],
        "client_id": NAVER_CLIENT_ID,
        "get_name": lambda c: c.get("name") or c.get("nickname"),
        "get_picture": lambda c: c.get("picture"),
        "get_email": lambda c: c.get("email"),
    },
}
USER_NAME_LENGTH_LIMIT = 100
USER_EMAIL_LENGTH_LIMIT = 254
PROVIDE_SUB_LENGTH_LIMIT = 255


class Provider(enum.StrEnum):
    GOOGLE = "google"
    APPLE = "apple"
    NAVER = "naver"


class UserStatus(enum.StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class InternalErrorCode(enum.IntEnum):
    def __new__(cls, value, text):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.text = text
        return obj

    INVALID_PROVIDER = 1000, "invalid identity provider"
    INVALID_ID_TOKEN = 1001, "invalid id token"
    UNREGISTERED_USER = 1002, "unregistered user"
    NO_AUTHORIZATION = 1003, "no authorization"
    UNCAUGHT = 9999, "server uncaught internal error"
