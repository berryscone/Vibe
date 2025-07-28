import uuid
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy import CheckConstraint
from vibe_api.db import db


gender_enum = ENUM('male', 'female', name='gender_type')

class UserModel(db.Model):
    __tablename__ = 'users'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.Text, unique=True, nullable=False)
    email = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    age = db.Column(db.Integer, CheckConstraint('age >= 0'), nullable=True)
    gender = db.Column(gender_enum, nullable=True)


class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserModel

user_schema = UserSchema()
users_schema = UserSchema(many=True)
