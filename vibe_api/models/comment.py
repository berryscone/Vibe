import uuid
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy.dialects.postgresql import UUID
from vibe_api.db import db


class CommentModel(db.Model):
    __tablename__ = 'comments'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = db.Column(db.Text, nullable=False)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    commented_on = db.Column(UUID(as_uuid=True), db.ForeignKey("posts.id", ondelete='CASCADE'), nullable=False, index=True)
    replied_on = db.Column(UUID(as_uuid=True), db.ForeignKey("comments.id", ondelete='CASCADE'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)


class CommentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = CommentModel
        include_fk = True
    
comment_schema = CommentSchema()
comments_schema = CommentSchema(many=True)
