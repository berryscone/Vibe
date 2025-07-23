import uuid
from flask_sqlalchemy import SQLAlchemy
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy import CheckConstraint

db = SQLAlchemy()

gender_enum = ENUM('male', 'female', name='gender_type', create_type=False)

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
