from uuid import UUID
from typing import Tuple
from http import HTTPStatus
from datetime import datetime, timezone

from flask_restful import Resource, reqparse, abort, request

from vibe_api.db import db
from vibe_api.models.user import UserModel, user_schema, USER_NAME_LENGTH_LIMIT
from vibe_api.models.registration_token import RegistrationTokenModel
from vibe_api.models.refresh_token import RefreshTokenModel
from vibe_api.constants import InternalErrorCode, UserStatus
from vibe_api.utils.auth_util import (
    issue_access_token,
    issue_refresh_token,
    require_auth,
    verify_dpop,
)
from vibe_api.utils.error_handling import make_error_response


KEY_NAME = "name"
KEY_REG_TOKEN = "reg_token"

post_user_parser = reqparse.RequestParser()
post_user_parser.add_argument(KEY_NAME, type=str, required=True)
post_user_parser.add_argument(KEY_REG_TOKEN, type=str, required=True)

put_user_parser = reqparse.RequestParser()
put_user_parser.add_argument(KEY_NAME, type=str)


class UserResource(Resource):
    method_decorators = {
        "get": [require_auth],
        "put": [require_auth],
        "delete": [require_auth],
    }

    def get(self, user_id):
        user = self._get_user_or_404(user_id)
        return user_schema.dump(user), HTTPStatus.OK.value

    def post(self):
        dpop = verify_dpop(expected_htu=request.url, expected_htm=request.method)
        jkt = dpop.get("jkt")

        try:
            name, reg_token = self._check_post_args_validity(parser=post_user_parser)
        except ValueError as e:
            db.session.rollback()
            return make_error_response(
                int_error_code=InternalErrorCode.INVALID_PROVIDER,
                message=str(e),
                http_status=HTTPStatus.BAD_REQUEST,
            )

        user = UserModel(
            name=name,
            status=UserStatus.ACTIVE,
            provider=reg_token.provider,
            provider_sub=reg_token.provider_sub,
            last_login_at=datetime.now(timezone.utc),
        )
        db.session.add(user)
        db.session.delete(reg_token)
        db.session.commit()

        access_token = issue_access_token(sub=user.provider_sub, jkt=jkt)
        refresh_token, refresh_token_expires_at = issue_refresh_token(
            sub=user.provider_sub
        )
        refresh_token_model = RefreshTokenModel(
            token_hash=refresh_token,
            jkt=jkt,
            created_by=user.id,
            expires_at=refresh_token_expires_at,
        )
        db.session.add(refresh_token_model)
        db.session.commit()

        return {
            "user": user_schema.dump(user),
            "access_token": access_token,
            "refresh_token": refresh_token,
        }, HTTPStatus.CREATED.value

    def put(self, user_id):
        user = self._get_user_or_404(user_id)

        try:
            name = self._check_put_args_validity(parser=put_user_parser)

            if name:
                user.name = name

            db.session.commit()
            return user_schema.dump(user), HTTPStatus.OK.value

        except ValueError as e:
            db.session.rollback()
            return make_error_response(
                int_error_code=InternalErrorCode.INVALID_PROVIDER,
                message=str(e),
                http_status=HTTPStatus.BAD_REQUEST,
            )

    def delete(self, user_id):
        user = self._get_user_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {}, HTTPStatus.NO_CONTENT.value

    def _get_user_or_404(self, user_id: str):
        try:
            user_uuid = UUID(user_id, version=4)
        except ValueError:
            abort(HTTPStatus.BAD_REQUEST.value, message="Invalid UUID format")
        return db.get_or_404(UserModel, user_uuid)

    def _check_post_args_validity(self, parser) -> Tuple[str, RegistrationTokenModel]:
        args = parser.parse_args()
        name = args[KEY_NAME]
        reg_token = args[KEY_REG_TOKEN]

        if name and len(name) > USER_NAME_LENGTH_LIMIT:
            raise ValueError("name is too long")

        reg_token_model = RegistrationTokenModel.query.filter(
            RegistrationTokenModel.token_hash == reg_token
        ).one_or_none()
        if reg_token_model is None:
            raise ValueError("invalid registration token")
        elif reg_token_model.expires_at < datetime.now(timezone.utc):
            raise ValueError("registration token expired")

        return name, reg_token_model

    def _check_put_args_validity(self, parser) -> str:
        args = parser.parse_args()
        name = args[KEY_NAME]

        if name and len(name) > USER_NAME_LENGTH_LIMIT:
            raise ValueError("name is too long")

        return name
