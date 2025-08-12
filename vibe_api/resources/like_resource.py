from uuid import UUID
from typing import Tuple
from sqlalchemy import event, delete
from flask_restful import Resource, abort, reqparse
from vibe_api.models.like import LikeModel, LikeType, like_schema 
from vibe_api.models.post import PostModel
from vibe_api.models.comment import CommentModel
from vibe_api.db import db


KEY_USER_ID = 'user_id'
KEY_TARGET_ID = 'target_id'
KEY_TARGET_TYPE = 'target_type'

like_post_parser = reqparse.RequestParser()
like_post_parser.add_argument(KEY_USER_ID, type=UUID, required=True)
like_post_parser.add_argument(KEY_TARGET_ID, type=str, required=True)
like_post_parser.add_argument(KEY_TARGET_TYPE, type=str, required=True)


class LikeResource(Resource):
    def get(self, like_id: str):
        like = self.get_like_or_404(like_id)
        return like_schema.dump(like), 200
    
    def post(self):
        try:
            user_id, target_id, target_type = self._check_post_args_validity()
            comment = LikeModel(
                user_id=user_id,
                target_id=target_id,
                target_type=target_type,
                )
            db.session.add(comment)
            db.session.commit()
            return like_schema.dump(comment), 201
        
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    def _check_post_args_validity(self) -> Tuple[UUID, str, str]:
        args = like_post_parser.parse_args()
        user_id = args[KEY_USER_ID]
        target_id = args[KEY_TARGET_ID]
        target_type = args[KEY_TARGET_TYPE]
        
        if target_type == LikeType.POST.value:
            model = PostModel
        elif target_type == LikeType.COMMENT.value:
            model = CommentModel
        else:
            raise Exception('invalid like type')
        
        target = db.session.get(model, target_id)
        if target is None:
            raise Exception('invalid target id')
        
        cnt_duplicate_like = db.session.query(LikeModel).filter(LikeModel.user_id == user_id, LikeModel.target_id == target_id).count()
        if cnt_duplicate_like > 0:
            raise Exception('duplicated like')
        
        return user_id, target_id, target_type

    def delete(self, like_id: str):
        like = self.get_like_or_404(like_id)

        try:
            db.session.delete(like)
            db.session.commit()
            return {}, 204
        
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    def get_like_or_404(self, like_id: str):
        try:
            like_id_uuid = UUID(like_id, version=4)
        except ValueError:
            abort(400, message="Invalid UUID format")
        return db.get_or_404(LikeModel, like_id_uuid)


@event.listens_for(PostModel, 'after_delete')
def delete_likes_of_deleted_post(mapper, connection, target):
    stmt = delete(LikeModel).where(LikeModel.target_id == target.id)
    connection.execute(stmt)

@event.listens_for(CommentModel, 'after_delete')
def delete_likes_of_deleted_comment(mapper, connection, target):
    stmt = delete(LikeModel).where(LikeModel.target_id == target.id)
    connection.execute(stmt)
