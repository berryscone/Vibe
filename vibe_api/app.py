from http import HTTPStatus

from flask import Flask
from flask_restful import Api
from werkzeug.exceptions import HTTPException

from vibe_api.constants import InternalErrorCode
from vibe_api.utils.error_handling import make_error_response
from vibe_api.config import ConfigProd, ConfigTest
from vibe_api.db import db
from vibe_api.resources.auth_resource import AuthResource
from vibe_api.resources.user_resource import UserResource
from vibe_api.resources.follow_resource import FollowResource
from vibe_api.resources.following_resource import FollowingsResource
from vibe_api.resources.follower_resource import FollowersResource
from vibe_api.resources.medium_resource import MediumResource
from vibe_api.resources.post_resource import PostResource
from vibe_api.resources.comment_resource import CommentResource
from vibe_api.resources.like_resource import LikeResource


def add_resources(app: Flask):
    api = Api(app)
    api.add_resource(AuthResource, "/auth/<string:provider>")
    api.add_resource(UserResource, "/api/user", "/api/user/<string:user_id>")

    api.add_resource(FollowResource, "/follow")
    api.add_resource(FollowingsResource, "/followings/<string:user_id>")
    api.add_resource(FollowersResource, "/followers/<string:user_id>")
    api.add_resource(MediumResource, "/media/<string:medium_id>")
    api.add_resource(PostResource, "/post", "/post/<string:post_id>")
    api.add_resource(CommentResource, "/comment", "/comment/<string:comment_id>")
    api.add_resource(LikeResource, "/like", "/like/<string:like_id>")


def create_app(is_test: bool = False):
    app = Flask(__name__)
    app.config.from_object(ConfigTest if is_test else ConfigProd)
    db.init_app(app)
    with app.app_context():
        # TODO: use database migration tool like Alembic instead of simple create_all() for production stage
        db.create_all()
    return app


app = create_app()
add_resources(app)


@app.errorhandler(Exception)
def handle_global_exception(e):
    if isinstance(e, HTTPException):
        return e
    db.session.rollback()
    return make_error_response(
        int_error_code=InternalErrorCode.UNCAUGHT,
        message=str(e),
        http_status=HTTPStatus.INTERNAL_SERVER_ERROR,
    )


if __name__ == "__main__":
    app.run(debug=True)
