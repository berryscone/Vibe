import uuid
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy.dialects.postgresql import UUID
from vibe_api.db import db


class RegistrationTokenModel(db.Model):
    __tablename__ = "registration_tokens"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_hash = db.Column(db.String, nullable=False, index=True)
    provider = db.Column(db.String, nullable=False)
    provider_sub = db.Column(db.String, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True), server_default=db.func.now(), nullable=False
    )
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    # TODO: register scheduler to remove expired tokens regularly


class RegistrationTokenSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = RegistrationTokenModel


registration_token_schema = RegistrationTokenSchema()
