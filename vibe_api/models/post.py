import uuid
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow_sqlalchemy.fields import Nested
from sqlalchemy.dialects.postgresql import UUID
from vibe_api.db import db
from vibe_api.models.medium import MediumScheme


class PostModel(db.Model):
    __tablename__ = 'posts'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caption = db.Column(db.Text, nullable=True)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    # https://docs.sqlalchemy.org/en/20/orm/relationships.html
    media = db.relationship("MediumModel", backref="post", order_by="MediumModel.order", cascade='delete')


class PostSchema(SQLAlchemyAutoSchema):
    media = Nested(MediumScheme, many=True)
    class Meta:
        model = PostModel
        include_fk = True

post_schema = PostSchema()
posts_schema = PostSchema(many=True)
