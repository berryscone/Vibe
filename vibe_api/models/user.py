import uuid
import enum
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy import CheckConstraint
from vibe_api.db import db


class GenderType(enum.StrEnum):
    MALE = "male"
    FEMALE = "female"

gender_type_enum = ENUM(GenderType.MALE, GenderType.FEMALE, name='gender_type')

USER_NAME_LENGTH_LIMIT = 100
USER_EMAIL_LENGTH_LIMIT = 254

class UserModel(db.Model):
    __tablename__ = 'users'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(USER_NAME_LENGTH_LIMIT), unique=True, nullable=False)
    email = db.Column(db.String(USER_EMAIL_LENGTH_LIMIT), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    age = db.Column(db.Integer, CheckConstraint('age >= 0'), nullable=True)
    gender = db.Column(gender_type_enum, nullable=True)


class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserModel

user_schema = UserSchema()
users_schema = UserSchema(many=True)
