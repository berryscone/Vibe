import uuid
import os
import enum
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.event import listens_for
from vibe_api.db import db

# from vibe_api.models.post import PostModel
from vibe_api.constants import OnDelete


class MediaType(enum.StrEnum):
    IMAGE = "image"
    VIDEO = "video"
    UNKNOWN = "unknown"


media_type_enum = ENUM(MediaType.IMAGE, MediaType.VIDEO, name="media_type")


class MediumModel(db.Model):
    __tablename__ = "media"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    media_url = db.Column(db.String, nullable=False)
    media_type = db.Column(media_type_enum, nullable=False)
    order = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        # TODO: enable media url validation
        # db.CheckConstraint(r"media_url ~ '^https?://[^\s/$.?#].[^\s]*$'", name='check_valid_url'),
    )


@listens_for(MediumModel, "after_delete")
def on_after_delete_medium(mapper, connection, target):
    # TODO: update delete code to remove media from remote storage
    if not target.media_url or not os.path.exists(target.media_url):
        return
    os.remove(target.media_url)


class MediumScheme(SQLAlchemyAutoSchema):
    class Meta:
        model = MediumModel
        include_fk = True


medium_scheme = MediumScheme()
media_scheme = MediumScheme(many=True)
