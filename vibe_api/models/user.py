import uuid
import enum
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import CheckConstraint
from vibe_api.db import db
from vibe_api.models.identity import IdentityModel


class UserGender(enum.StrEnum):
    MALE = "male"
    FEMALE = "female"

class UserStatus(enum.StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


USER_NAME_LENGTH_LIMIT = 100
USER_EMAIL_LENGTH_LIMIT = 254

class UserModel(db.Model):
    __tablename__ = 'users'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(USER_NAME_LENGTH_LIMIT), unique=True, nullable=False)
    email = db.Column(db.String(USER_EMAIL_LENGTH_LIMIT), nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    age = db.Column(db.Integer, CheckConstraint('age >= 0'), nullable=True)
    gender = db.Column(db.Enum(UserGender), nullable=True)
    status = db.Column(db.Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    identities = db.relationship(IdentityModel, backref="user", cascade='delete, delete-orphan')


class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserModel

user_schema = UserSchema()
users_schema = UserSchema(many=True)
