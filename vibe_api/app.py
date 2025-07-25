from flask import Flask
from flask_restful import Api
from vibe_api.config import Config
from vibe_api.resources.user_resource import UserResource
from vibe_api.resources.follow_resource import FollowResource
from vibe_api.resources.following_resource import FollowingsResource
from vibe_api.resources.follower_resource import FollowersResource
from vibe_api.db import db


app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
with app.app_context():
    db.create_all()

api = Api(app)
api.add_resource(UserResource, '/user', '/user/<string:user_id>')

if __name__ == "__main__":
    app.run(debug=True)
