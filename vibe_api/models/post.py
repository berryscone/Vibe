import uuid
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.event import listens_for
from marshmallow_sqlalchemy.fields import Nested
from vibe_api.db import db
from vibe_api.models.user import UserModel
from vibe_api.models.medium import MediumModel, MediumScheme

POST_CAPTION_LENGTH_LIMIT = 300


class PostModel(db.Model):
    __tablename__ = "posts"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caption = db.Column(db.String(POST_CAPTION_LENGTH_LIMIT), nullable=True)
    created_by = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(UserModel.id, ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = db.Column(
        db.DateTime(timezone=True), server_default=db.func.now(), nullable=False
    )
    media = db.relationship(
        MediumModel,
        backref="post",
        order_by="MediumModel.order",
        cascade="delete, delete-orphan",
    )


class PostSchema(SQLAlchemyAutoSchema):
    media = Nested(MediumScheme, many=True)

    class Meta:
        model = PostModel
        include_fk = True


post_schema = PostSchema()
posts_schema = PostSchema(many=True)
