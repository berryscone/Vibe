from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field
from sqlalchemy.dialects.postgresql import UUID
from vibe_api.db import db


class FollowModel(db.Model):
    __tablename__ = 'follows'

    user_from = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user_to = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)

    __table_args__ = (
        db.PrimaryKeyConstraint('user_from', 'user_to'),
        db.CheckConstraint('user_from != user_to', name='check_not_self_follow'),
        db.Index('idx_follows_user_from', 'user_from'),
        db.Index('idx_follows_user_to', 'user_to'),
    )


class FollowSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = FollowModel
        include_fk = True
    
follow_schema = FollowSchema()
follows_schema = FollowSchema(many=True)
