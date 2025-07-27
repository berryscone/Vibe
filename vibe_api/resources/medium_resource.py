from uuid import UUID
from flask_restful import Resource, abort
from vibe_api.models.medium import MediumModel, medium_scheme
from vibe_api.db import db


class MediumResource(Resource):
    def get(self, medium_id: str):
        try:
            medium_id_uuid = UUID(medium_id, version=4)
        except ValueError:
            abort(400, message="Invalid UUID format")
        medium = db.get_or_404(MediumModel, medium_id_uuid)
        return medium_scheme.dump(medium), 200
