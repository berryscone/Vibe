from datetime import datetime, timezone
from uuid import UUID
from flask_restful import Resource, abort, reqparse
from vibe_api.models.comment import CommentModel, comment_schema
from vibe_api.db import db


KEY_TEXT = 'text'
KEY_CREATED_BY = 'created_by'
KEY_COMMENTED_ON = 'commented_on'
KEY_REPLIED_ON = 'replied_on'

comment_post_parser = reqparse.RequestParser()
comment_post_parser.add_argument(KEY_CREATED_BY, type=UUID, required=True)
comment_post_parser.add_argument(KEY_TEXT, type=str, required=True)
comment_post_parser.add_argument(KEY_COMMENTED_ON, type=UUID, required=True)
comment_post_parser.add_argument(KEY_REPLIED_ON, type=UUID, required=False)

comment_put_parser = reqparse.RequestParser()
comment_put_parser.add_argument(KEY_TEXT, type=str, required=True)


class CommentResource(Resource):
    def get(self, comment_id: str):
        comment = self.get_comment_or_404(comment_id)
        return comment_schema.dump(comment), 200
    
    def post(self):
        args = comment_post_parser.parse_args()

        try:
            created_by = args[KEY_CREATED_BY]
            commented_on = args[KEY_COMMENTED_ON]
            replied_on = args[KEY_REPLIED_ON]
            text = args[KEY_TEXT]

            comment = CommentModel(
                created_by=created_by,
                commented_on=commented_on,
                replied_on=replied_on,
                text=text,
                )
            db.session.add(comment)
            db.session.commit()
            return comment_schema.dump(comment), 201
        
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    def put(self, comment_id: str):
        comment = self.get_comment_or_404(comment_id)
        args = comment_put_parser.parse_args()
        
        try:
            text = args[KEY_TEXT]
            comment.text = text
            db.session.commit()
            return comment_schema.dump(comment), 200
        
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500


    def delete(self, comment_id: str):
        comment = self.get_comment_or_404(comment_id)

        if comment.replied_on:
            return self._delete_reply(comment)
        else:
            return self._delete_comment(comment)

    def _delete_comment(self, comment: CommentModel):
        try:
            cnt_replies_on_this_comment = db.session.query(CommentModel).filter(CommentModel.replied_on == comment.id).count()
            if cnt_replies_on_this_comment > 0:
                comment.deleted_at = datetime.now(timezone.utc)
                comment.text = "deleted comment"
                db.session.commit()
                return comment_schema.dump(comment), 200
            else:
                db.session.delete(comment)
                db.session.commit()
                return {}, 204
        
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    def _delete_reply(self, comment: CommentModel):
        try:
            parent_comment = db.session.get(CommentModel, comment.replied_on)
            db.session.delete(comment)

            cnt_replies_on_parent_comment = db.session.query(CommentModel).filter(CommentModel.replied_on == parent_comment.id).count()
            if cnt_replies_on_parent_comment == 0 and parent_comment.deleted_at:
                db.session.delete(parent_comment)

            db.session.commit()
            return {}, 204
        
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    def get_comment_or_404(self, comment_id: str):
        try:
            comment_id_uuid = UUID(comment_id, version=4)
        except ValueError:
            abort(400, message="Invalid UUID format")
        return db.get_or_404(CommentModel, comment_id_uuid)
