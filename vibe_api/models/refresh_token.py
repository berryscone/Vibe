import uuid
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy.dialects.postgresql import UUID
from vibe_api.db import db
from vibe_api.models.user import UserModel
from vibe_api.constants import OnDelete


class RefreshTokenModel(db.Model):
    __tablename__ = 'refresh_tokens'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_hash = db.Column(db.String, nullable=False)
    jkt = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey(UserModel.id, ondelete=OnDelete.CASCADE), nullable=False, index=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)


class RefreshTokenSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = RefreshTokenModel

refresh_token_schema = RefreshTokenSchema()
