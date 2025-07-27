from uuid import UUID
from flask_restful import Resource, reqparse, abort
from vibe_api.models.follow import FollowModel, follow_schema
from vibe_api.db import db


follow_parser = reqparse.RequestParser()
follow_parser.add_argument('user_from', type=str, required=True)
follow_parser.add_argument('user_to', type=str, required=True)

class FollowResource(Resource):
    def get(self):
        args = follow_parser.parse_args()
        follow = self.get_follow_or_404(args['user_from'], args['user_to'])
        return follow_schema.dump(follow), 200

    def post(self):
        args = follow_parser.parse_args()

        try:
            follow = FollowModel(
                user_from=args['user_from'],
                user_to=args['user_to'],
            )
            db.session.add(follow)
            db.session.commit()
            return follow_schema.dump(follow), 201
        except Exception as ie:
            db.session.rollback()
            return {"error": str(ie)}, 500
        
    def delete(self):
        args = follow_parser.parse_args()
        follow = self.get_follow_or_404(args['user_from'], args['user_to'])

        try:
            db.session.delete(follow)
            db.session.commit()
            return {}, 204
        except Exception as ie:
            db.session.rollback()
            return {"error": str(ie)}, 500
    
    def get_follow_or_404(self, user_from: str, user_to: str):
        try:
            user_from_uuid = UUID(user_from, version=4)
            user_to_uuid = UUID(user_to, version=4)
        except ValueError:
            abort(400, message="Invalid UUID format")
        return db.get_or_404(FollowModel, (user_from_uuid, user_to_uuid))
