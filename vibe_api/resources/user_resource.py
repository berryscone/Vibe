from uuid import UUID
from flask_restful import Resource, reqparse, abort
from vibe_api.models.user import UserModel, user_schema
from vibe_api.db import db


post_user_parser = reqparse.RequestParser()
post_user_parser.add_argument('name', type=str, required=True, help='Name is required')
post_user_parser.add_argument('email', type=str, required=True, help='Valid email is required')
post_user_parser.add_argument('age', type=int, required=False)
post_user_parser.add_argument('gender', type=str, required=False)

put_user_parser = reqparse.RequestParser()
put_user_parser.add_argument('name', type=str)
put_user_parser.add_argument('email', type=str)
put_user_parser.add_argument('age', type=int)
put_user_parser.add_argument('gender', type=str)

class UserResource(Resource):
    def abort_if_user_id_is_invalid_or_return_user(self, user_id: str):
        try:
            user_uuid = UUID(user_id, version=4)
        except ValueError:
            abort(400, message="Invalid UUID format")
        return db.get_or_404(UserModel, user_uuid)

    def get(self, user_id):
        user = self.abort_if_user_id_is_invalid_or_return_user(user_id)
        return user_schema.dump(user), 200

    def post(self):
        args = post_user_parser.parse_args()

        try:
            user = UserModel(
                name=args['name'],
                email=args['email'],
                age=args['age'],
                gender=args['gender']
            )
            db.session.add(user)
            db.session.commit()
            return user_schema.dump(user), 201
        except Exception as ie:
            db.session.rollback()
            return {"error": str(ie)}, 500
        
    def put(self, user_id):
        user = self.abort_if_user_id_is_invalid_or_return_user(user_id)
        args = put_user_parser.parse_args()
        
        if args['name']:
            user.name = args['name']
        if args['email']:
            user.email = args['email']
        if args['age']:
            user.age = args['age']
        if args['gender']:
            user.gender = args['gender']

        try:
            db.session.commit()
            return user_schema.dump(user), 200
        except Exception as ie:
            db.session.rollback()
            return {"error": str(ie)}, 500

    def delete(self, user_id):
        user = self.abort_if_user_id_is_invalid_or_return_user(user_id)

        try:
            db.session.delete(user)
            db.session.commit()
            return {}, 204
        except Exception as ie:
            db.session.rollback()
            return {"error": str(ie)}, 500
