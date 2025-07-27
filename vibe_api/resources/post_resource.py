import os
import time
from uuid import UUID, uuid4
from flask_restful import Resource, abort, reqparse, request
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from vibe_api.models.post import PostModel, post_schema
from vibe_api.models.medium import MediumModel, MEDIA_TYPE_IMAGE, MEDIA_TYPE_VIDEO, MEDIA_TYPE_UNKNOWN
from vibe_api.db import db


post_post_parser = reqparse.RequestParser()
post_post_parser.add_argument('created_by', type=UUID, required=True, location='form')
post_post_parser.add_argument('caption', type=str, required=False, location='form')
post_post_parser.add_argument('media', type=FileStorage, required=True, location='files', action='append')

UPLOAD_FOLDER = 'media/'
ALLOWED_IMAGE_EXTENSIONS = { 'jpg', 'jpeg', 'png', 'webp' }
ALLOWED_VIDEO_EXTENSIONS = { 'mp4', 'mov', }
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS

def generate_unique_filename(original_filename):
    filename = secure_filename(original_filename)
    timestamp = int(time.time() * 1000)
    random_id = uuid4().hex[:8]
    ext = os.path.splitext(filename)[1]
    return f"{timestamp}_{random_id}{ext}"

class PostResource(Resource):
    def get(self, post_id: str):
        post = self.get_post_or_404(post_id)
        return post_schema.dump(post), 200
    
    def post(self):
        args = post_post_parser.parse_args()

        files = args['media']
        if not isinstance(files, list):
            files = [files]

        saved_file_paths = []
        try:
            post = PostModel(
                created_by=args['created_by'],
                caption=args.get('caption'),
                )
            db.session.add(post)
            db.session.flush()

            order = 0
            for file in files:
                if not file:
                    continue
                if not self.allowed_file(file.filename):
                    continue

                unique_filename = generate_unique_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
                file.save(filepath)
                saved_file_paths.append(filepath)

                media_type = self.get_media_type_from_filename(unique_filename)
                media = MediumModel(
                    post_id=post.id,
                    media_url=filepath,
                    media_type=media_type,
                    order=order
                    )
                db.session.add(media)
                order += 1

            db.session.commit()
            return post_schema.dump(post), 201
        except Exception as e:
            db.session.rollback()
            for saved_file_path in saved_file_paths:
                os.remove(saved_file_path)
            return {"error": str(e)}, 500

    def delete(self, post_id: str):
        post = self.get_post_or_404(post_id)
        try:
            db.session.delete(post)
            db.session.commit()
            return {}, 204
        except Exception as ie:
            db.session.rollback()
            return {"error": str(ie)}, 500

    def get_post_or_404(self, post_id: str):
        try:
            post_id_uuid = UUID(post_id, version=4)
        except ValueError:
            abort(400, message="Invalid UUID format")
        return db.get_or_404(PostModel, post_id_uuid)

    def get_media_type_from_filename(self, filename: str):
        if '.' not in filename:
            return MEDIA_TYPE_UNKNOWN
        ext = filename.split('.')[1].lower()
        if ext in ALLOWED_VIDEO_EXTENSIONS:
            return MEDIA_TYPE_VIDEO
        elif ext in ALLOWED_IMAGE_EXTENSIONS:
            return MEDIA_TYPE_IMAGE
        return MEDIA_TYPE_UNKNOWN

    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

