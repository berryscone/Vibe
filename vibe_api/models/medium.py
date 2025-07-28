import uuid
import os
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.event import listens_for
from vibe_api.db import db

MEDIA_TYPE_IMAGE = 'image'
MEDIA_TYPE_VIDEO = 'video'
MEDIA_TYPE_UNKNOWN = 'unknown'
media_type_enum = ENUM(MEDIA_TYPE_IMAGE, MEDIA_TYPE_VIDEO, name='media_type')

class MediumModel(db.Model):
    __tablename__ = 'media'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = db.Column(UUID(as_uuid=True), db.ForeignKey("posts.id", ondelete='CASCADE'), nullable=False, index=True)
    media_url = db.Column(db.String, nullable=False)
    media_type = db.Column(media_type_enum, nullable=False)
    order = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        # db.CheckConstraint(r"media_url ~ '^https?://[^\s/$.?#].[^\s]*$'", name='check_valid_url'),
    )

    def delete_local_file(self):
        if not self.media_url or not os.path.exists(self.media_url):
            return
        os.remove(self.media_url)

@listens_for(MediumModel, 'before_delete')
def delete_file_on_row_delete(mapper, connection, target):
    target.delete_local_file()


class MediumScheme(SQLAlchemyAutoSchema):
    class Meta:
        model = MediumModel
        include_fk = True

medium_scheme = MediumScheme()
media_scheme = MediumScheme(many=True)
