from uuid import UUID
from flask_restful import Resource, abort
from vibe_api.models.user import UserModel, users_schema
from vibe_api.models.follow import FollowModel, follows_schema
from vibe_api.db import db


class FollowersResource(Resource):
    def get(self, user_id):
        try:
            user_id_uuid = UUID(user_id, version=4)
        except ValueError:
            abort(400, message="Invalid UUID format")
        followings = db.session.query(UserModel.id, UserModel.name)\
            .join(FollowModel, UserModel.id == FollowModel.user_from)\
            .filter(FollowModel.user_to == user_id_uuid)\
            .all()
        return users_schema.dump(followings), 200
