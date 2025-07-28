import os
import time
from uuid import UUID, uuid4
from sqlalchemy import and_
from flask_restful import Resource, abort, reqparse, request
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from vibe_api.models.post import PostModel, post_schema
from vibe_api.models.medium import MediumModel, MEDIA_TYPE_IMAGE, MEDIA_TYPE_VIDEO, MEDIA_TYPE_UNKNOWN
from vibe_api.db import db


KEY_CREATED_BY = 'created_by'
KEY_CAPTION = 'caption'
KEY_MEDIA = 'media'
KEY_MEDIA_TO_DELETE = 'media_to_delete'
KEY_MEDIA_TO_INSERT = 'media_to_insert'
KEY_INSERTED_MEDIA_POSITIONS = 'inserted_media_positions'
KEY_MEDIA_ORDER = 'media_order'

post_post_parser = reqparse.RequestParser()
post_post_parser.add_argument(KEY_CREATED_BY, type=UUID, required=True, location='form')
post_post_parser.add_argument(KEY_CAPTION, type=str, required=False, location='form')
post_post_parser.add_argument(KEY_MEDIA, type=FileStorage, required=True, location='files', action='append', default=[])

post_put_parser = reqparse.RequestParser()
post_put_parser.add_argument(KEY_CAPTION, type=str, required=False, location='form')
post_put_parser.add_argument(KEY_MEDIA_TO_DELETE, type=str, required=False, location='form', action='append', default=[])
post_put_parser.add_argument(KEY_MEDIA_TO_INSERT, type=FileStorage, required=False, location='files', action='append', default=[])
post_put_parser.add_argument(KEY_INSERTED_MEDIA_POSITIONS, type=int, required=False, location='form', action='append', default=[])
post_put_parser.add_argument(KEY_MEDIA_ORDER, type=str, required=False, location='form', action='append')

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

        files = args[KEY_MEDIA]
        saved_file_paths = []
        try:
            post = PostModel(
                created_by=args[KEY_CREATED_BY],
                caption=args.get(KEY_CAPTION),
                )
            db.session.add(post)
            db.session.flush()

            order = 0
            for file in files:
                if not file:
                    raise Exception(f'unable to get file - {file.filename}')
                if not self.allowed_file(file.filename):
                    raise Exception(f'not allowed file format - {file.filename}')

                unique_filename = generate_unique_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
                file.save(filepath)
                saved_file_paths.append(filepath)

                medium = MediumModel(
                    post_id=post.id,
                    media_url=filepath,
                    media_type=self.get_media_type_from_filename(unique_filename),
                    order=order)
                db.session.add(medium)
                order += 1

            db.session.commit()
            return post_schema.dump(post), 201
        
        except Exception as e:
            db.session.rollback()
            for saved_file_path in saved_file_paths:
                os.remove(saved_file_path)
            return {"error": str(e)}, 500

    def put(self, post_id):
        post = self.get_post_or_404(post_id)
        args = post_put_parser.parse_args()
        saved_file_paths = []

        try:
            # handle caption update
            if args[KEY_CAPTION]:
                # TODO: check invalid/inappropriate words or expressions
                post.caption = args[KEY_CAPTION]

            # handle media deletion
            media_to_delete = args[KEY_MEDIA_TO_DELETE]
            if media_to_delete:
                number_of_media_in_the_post = db.session.query(MediumModel).filter(MediumModel.post_id == post.id).count()
                if len(media_to_delete) == number_of_media_in_the_post:
                    raise Exception('cannot delete every media on a post')
                
                for medium_id in media_to_delete:
                    medium_id_uuid = UUID(medium_id, version=4)
                    medium = db.session.query(MediumModel).filter(and_(MediumModel.id == medium_id_uuid, MediumModel.post_id == post.id)).first()
                    if not medium:
                        raise Exception(f"unable to find medium '{medium_id}'")
                    db.session.delete(medium)

            # handle media insertion
            media_to_insert = args[KEY_MEDIA_TO_INSERT]
            inserted_media_positions = args[KEY_INSERTED_MEDIA_POSITIONS]
            if media_to_insert:
                if len(media_to_insert) != len(inserted_media_positions):
                    raise Exception(f"invalid argument - length of '{KEY_MEDIA_TO_INSERT}' and '{KEY_INSERTED_MEDIA_POSITIONS}' are different")
                if len(inserted_media_positions) != len(set(inserted_media_positions)):
                    raise Exception(f"invalid argument - duplicated positions on '{KEY_INSERTED_MEDIA_POSITIONS}'")
                if any(pos < 0 for pos in inserted_media_positions):
                    raise Exception(f"invalid argument - negative positions on '{KEY_INSERTED_MEDIA_POSITIONS}'")
                # TODO: check invalid position from inserted_media_positions
                
                max_order = db.session.query(db.func.max(MediumModel.order)).filter(MediumModel.post_id == post.id).scalar()
                for i, pos in enumerate(inserted_media_positions):
                    if pos <= max_order:
                        db.session.query(MediumModel).filter(
                            MediumModel.post_id == post.id,
                            MediumModel.order >= pos
                        ).update({"order": MediumModel.order + 1}, synchronize_session=False)

                for i, file in enumerate(media_to_insert):
                    if not file:
                        raise Exception(f'unable to get file - {file.filename}')
                    if not self.allowed_file(file.filename):
                        raise Exception(f'not allowed file format - {file.filename}')

                    unique_filename = generate_unique_filename(file.filename)
                    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
                    file.save(filepath)
                    saved_file_paths.append(filepath)

                    medium = MediumModel(
                        post_id=post.id,
                        media_url=filepath,
                        media_type=self.get_media_type_from_filename(unique_filename),
                        order=inserted_media_positions[i])
                    db.session.add(medium)

            # handle media reordering
            media_order = args[KEY_MEDIA_ORDER]
            if media_order:
                for index, media_id in enumerate(media_order):
                    media_id_uuid = UUID(media_id, version=4)
                    media = db.session.query(MediumModel).filter(and_(MediumModel.id == media_id_uuid, MediumModel.post_id == post.id)).first()
                    if media:
                        media.order = index

            db.session.commit()
            return post_schema.dump(post), 200
        
        except Exception as e:
            db.session.rollback()
            for saved_file_path in saved_file_paths:
                if os.path.exists(saved_file_path):
                    os.remove(saved_file_path)
            return {"error": str(e)}, 500

    def delete(self, post_id: str):
        post = self.get_post_or_404(post_id)
        try:
            db.session.delete(post)
            db.session.commit()
            return {}, 204
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

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
