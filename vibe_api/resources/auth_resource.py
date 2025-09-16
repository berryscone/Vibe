import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from http import HTTPStatus

from sqlalchemy import and_
from flask_restful import Resource, reqparse, request

from vibe_api.db import db
from vibe_api.models.user import UserModel, UserStatus, user_schema
from vibe_api.models.registration_token import RegistrationTokenModel
from vibe_api.models.refresh_token import RefreshTokenModel
from vibe_api.utils.auth_util import (
    issue_access_token,
    issue_refresh_token,
    verify_id_token_with_jwks,
    verify_dpop,
)
from vibe_api.utils.error_handling import make_error_response
from vibe_api.constants import InternalErrorCode, PROVIDERS


KEY_ID_TOKEN = "id_token"
KEY_AUDIENCE = "audience"
KEY_REFRESH_TOKEN = "refresh_token"

auth_post_parser = reqparse.RequestParser()
auth_post_parser.add_argument(KEY_ID_TOKEN, type=str, required=True)
auth_post_parser.add_argument(KEY_AUDIENCE, type=str, required=True)

auth_put_parser = reqparse.RequestParser()
auth_put_parser.add_argument(KEY_REFRESH_TOKEN, type=str, required=True)


class AuthResource(Resource):
    def post(self, provider: str):
        dpop = verify_dpop(expected_htu=request.url, expected_htm=request.method)
        jkt = dpop.get("jkt")

        provider = provider.lower()
        if provider not in PROVIDERS:
            return make_error_response(
                int_error_code=InternalErrorCode.INVALID_PROVIDER,
                message=f"unsupported provider: {provider}",
                http_status=HTTPStatus.BAD_REQUEST,
            )

        args = auth_post_parser.parse_args()
        id_token = args[KEY_ID_TOKEN]
        audience = args[KEY_AUDIENCE]

        try:
            claims = verify_id_token_with_jwks(
                provider_key=provider,
                id_token=id_token,
                audience=audience,
            )
        except ValueError as e:
            return make_error_response(
                int_error_code=InternalErrorCode.INVALID_ID_TOKEN,
                message=str(e),
                http_status=HTTPStatus.UNAUTHORIZED,
            )

        provider_sub = claims.get("sub")
        user = UserModel.query.filter(
            and_(UserModel.provider == provider, UserModel.provider_sub == provider_sub)
        ).one_or_none()

        if user is None:
            reg_token = secrets.token_urlsafe(64)
            hashed_reg_token = hashlib.sha256(reg_token.encode()).hexdigest()
            reg_token_model = RegistrationTokenModel(
                token_hash=hashed_reg_token,
                provider=provider,
                provider_sub=provider_sub,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            )
            db.session.add(reg_token_model)
            db.session.commit()
            return {"reg_token": hashed_reg_token}, HTTPStatus.ACCEPTED.value

        access_token = issue_access_token(sub=provider_sub, jkt=jkt)
        refresh_token, refresh_token_expires_at = issue_refresh_token(sub=provider_sub)
        refresh_token_model = RefreshTokenModel(
            token_hash=refresh_token,
            jkt=jkt,
            created_by=user.id,
            expires_at=refresh_token_expires_at,
        )
        db.session.add(refresh_token_model)

        user.status = UserStatus.ACTIVE
        user.last_login_at = datetime.now(timezone.utc)
        db.session.commit()

        return {
            "user": user_schema.dump(user),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "refresh_token_expires_at": refresh_token_expires_at.timestamp(),
        }, HTTPStatus.OK.value

    def put(self):
        # TODO: implement refreshing access token
        """
        access token도 같이 받아서 refresh token과 access token의 user_id 또는 sub 일치 확인
        AT를 refresh하면 AT/RT 모두 revoke 시키고 새로운 AT/RT 발급
        refresh token을 제공한 놈이 진짜 소유자인지 증명하기 위해 DPop사용
        DPop을 사용하기 위해서는 처음 AT/RT 발급 받을 때 client의 public key를 server에게 제공했어야 함


        1. client는 public/private key pair를 생성
        2. client가 처음 로그인 할 때 DPop JWT의 header에 JWK 형식의 public key를 포함하고
            private key로 서명된 signature와 함께 server에 전달
        3. server는 공유된 public key를 이용해 서명을 확인하고 jkt를 DB에 저장
        4. client는 모든 요청에 DPop JWT를 만들어서 함께 전달
        5. refresh 요청도 DPop JWT가 포함되므로 AT/RT를 만들었던 사용자가 요청한것임을 증명 가능

        htu : HTTP URI - full URI of the request
        htm : HTTP Method
        iat : Issued At
        jti : JWT ID - random UUID
        cnf : Confirmation
        jwk : Json Web Key
        jkt : JWK(Json Wek Key) Thumbprint
        jwt : Json Web Token
        """
        pass

    def delete(self):
        # access token is required
        # remove refresh token
        # change user status to UserStatus.INACTIVE
        pass
