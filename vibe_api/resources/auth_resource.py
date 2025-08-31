import os
from datetime import datetime, timezone

from flask_restful import Resource, reqparse

from vibe_api.models.identity import IdentityModel
from vibe_api.models.user import user_schema
from vibe_api.db import db
from vibe_api.utils.auth_util import issue_access_token, verify_id_token_with_jwks, PROVIDERS


GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ISSUER = os.getenv("JWT_ISSUER")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE")
JWT_EXPIRE_MIN = int(os.getenv("JWT_EXPIRE_MIN"))

auth_post_parser = reqparse.RequestParser()
auth_post_parser.add_argument("id_token", type=str, required=True)
auth_post_parser.add_argument("audience", type=str, required=True)

class AuthResource(Resource):
    def post(self, provider: str):
        provider = provider.lower()
        if provider not in PROVIDERS:
            return {"error": f"unsupported provider: {provider}"}, 400

        args = auth_post_parser.parse_args()
        id_token = args["id_token"]
        audience = args["audience"]

        try:
            claims = verify_id_token_with_jwks(
                id_token=id_token,
                provider_key=provider,
                audience=audience,
            )
        except ValueError as e:
            return {"error": str(e)}, 401
        
        try:
            provider_sub = claims.get("sub")
            identity = db.session.query(IdentityModel).filter_by(provider=provider, provider_sub=provider_sub).one_or_none()
            if not identity:
                return {"error": "user not registered"}, 401
            
            identity.last_login_at = datetime.now(timezone.utc)
            access_token = issue_access_token(sub=identity.user_id)
            db.session.commit()
            return {"user": user_schema.dump(identity.user), "access_token": access_token}, 200

        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500
