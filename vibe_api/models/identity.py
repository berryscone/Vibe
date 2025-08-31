import uuid
from enum import StrEnum

from sqlalchemy.dialects.postgresql import UUID
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from vibe_api.db import db
from vibe_api.models.mixin import TimestampMixin
from vibe_api.constants import OnDelete

class Provider(StrEnum):
    GOOGLE = "google"
    APPLE  = "apple"
    NAVER  = "naver"


PROVIDE_SUB_LENGTH_LIMIT = 255

class IdentityModel(db.Model, TimestampMixin):
    __tablename__ = "identities"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id", ondelete=OnDelete.CASCADE), nullable=False, index=True)
    provider = db.Column(db.Enum(Provider), nullable=False)
    provider_sub = db.Column(db.String(PROVIDE_SUB_LENGTH_LIMIT), nullable=False)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)
    

class IdentitySchema(SQLAlchemyAutoSchema):
    class Meta:
        model = IdentityModel

identity_schema = IdentitySchema()
identities_schema = IdentitySchema(many=True)
