from flask import Flask
from flask_restful import Api
from flask_marshmallow import Marshmallow
from vibe_api.config import Config
from vibe_api.resources.user_resource import UserResource
from vibe_api.models.user import db


app = Flask(__name__)
ma = Marshmallow(app)
app.config.from_object(Config)
db.init_app(app)
api = Api(app)

api.add_resource(UserResource, '/user', '/user/<string:user_id>')

if __name__ == "__main__":
    app.run(debug=True)
