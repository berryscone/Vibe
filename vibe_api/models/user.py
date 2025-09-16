import uuid

from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy.dialects.postgresql import UUID

from vibe_api.db import db
from vibe_api.constants import (
    UserStatus,
    Provider,
    USER_NAME_LENGTH_LIMIT,
    PROVIDE_SUB_LENGTH_LIMIT,
)


class UserModel(db.Model):
    __tablename__ = "users"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(USER_NAME_LENGTH_LIMIT), unique=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True), server_default=db.func.now(), nullable=False
    )
    status = db.Column(
        db.Enum(UserStatus),
        default=UserStatus.ACTIVE,
        nullable=False,
    )

    provider = db.Column(db.Enum(Provider), nullable=False)
    provider_sub = db.Column(db.String(PROVIDE_SUB_LENGTH_LIMIT), nullable=False)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)


class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserModel


user_schema = UserSchema()
users_schema = UserSchema(many=True)
