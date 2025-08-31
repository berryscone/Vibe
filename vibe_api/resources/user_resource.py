from uuid import UUID
from typing import Tuple

from email_validator import validate_email
from flask_restful import Resource, reqparse, abort

from vibe_api.models.user import UserModel, UserGender, user_schema, USER_NAME_LENGTH_LIMIT, USER_EMAIL_LENGTH_LIMIT
from vibe_api.db import db
from vibe_api.utils.auth_util import require_auth


KEY_NAME = 'name'
KEY_EMAIL = 'email'
KEY_AGE = 'age'
KEY_GENDER = 'gender'

post_user_parser = reqparse.RequestParser()
post_user_parser.add_argument(KEY_NAME, type=str, required=True)
post_user_parser.add_argument(KEY_EMAIL, type=str, required=True)
post_user_parser.add_argument(KEY_AGE, type=int, required=False)
post_user_parser.add_argument(KEY_GENDER, type=str, required=False)

put_user_parser = reqparse.RequestParser()
put_user_parser.add_argument(KEY_NAME, type=str)
put_user_parser.add_argument(KEY_EMAIL, type=str)
put_user_parser.add_argument(KEY_AGE, type=int)
put_user_parser.add_argument(KEY_GENDER, type=str)

class UserResource(Resource):
    method_decorators = {
        'get': [require_auth],
        'put': [require_auth],
        'delete': [require_auth],
    }

    def get(self, user_id):
        user = self._get_user_or_404(user_id)
        return user_schema.dump(user), 200

    def post(self):
        try:
            name, email, age, gender = self._check_args_validity(parser=post_user_parser)
            user = UserModel(
                name=name,
                email=email,
                age=age,
                gender=gender
            )
            db.session.add(user)
            db.session.commit()
            return user_schema.dump(user), 201
        
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500
        
    def put(self, user_id):
        user = self._get_user_or_404(user_id)

        try:
            name, email, age, gender = self._check_args_validity(parser=put_user_parser)
            
            if name:
                user.name = name
            if email:
                user.email = email
            if age:
                user.age = age
            if gender:
                user.gender = gender

            db.session.commit()
            return user_schema.dump(user), 200
        
        except Exception as ie:
            db.session.rollback()
            return {"error": str(ie)}, 500

    def delete(self, user_id):
        user = self._get_user_or_404(user_id)

        try:
            db.session.delete(user)
            db.session.commit()
            return {}, 204
        
        except Exception as ie:
            db.session.rollback()
            return {"error": str(ie)}, 500
        
    def _get_user_or_404(self, user_id: str):
        try:
            user_uuid = UUID(user_id, version=4)
        except ValueError:
            abort(400, message="Invalid UUID format")
        return db.get_or_404(UserModel, user_uuid)

    def _check_args_validity(self, parser) -> Tuple[str, str, str, str]:
        args = parser.parse_args()
        name = args[KEY_NAME]
        email = args[KEY_EMAIL]
        age = args[KEY_AGE]
        gender = args[KEY_GENDER]

        if name and len(name) > USER_NAME_LENGTH_LIMIT:
            raise Exception('name is too long')
        
        if email and not validate_email(email):
            raise Exception('invalid email')

        if age and age < 0:
            raise Exception('invalid age')
        
        if gender and gender not in UserGender:
            raise Exception('invalid gender')

        return name, email, age, gender
