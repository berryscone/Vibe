import uuid
import enum
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy.dialects.postgresql import UUID, ENUM
from vibe_api.db import db
from vibe_api.models.user import UserModel
from vibe_api.constants import OnDelete


class LikeType(enum.StrEnum):
    POST = "post"
    COMMENT = "comment"

like_type_enum = ENUM(LikeType.POST, LikeType.COMMENT, name='like_type')

class LikeModel(db.Model):
    __tablename__ = 'likes'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey(UserModel.id, ondelete=OnDelete.CASCADE), nullable=False, index=True)
    target_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    target_type = db.Column(like_type_enum, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'target_id', name='unique_like_per_user'),
    )


class LikeSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = LikeModel
        include_fk = True
    
like_schema = LikeSchema()
likes_schema = LikeSchema(many=True)
