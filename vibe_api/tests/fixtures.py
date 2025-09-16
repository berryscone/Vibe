import logging

import pytest
from flask_migrate import upgrade

from vibe_api.app import create_app, add_resources
from vibe_api.db import db


@pytest.fixture(scope="session")
def test_app():
    app = create_app(is_test=True)
    add_resources(app)
    yield app


@pytest.fixture(scope="module")
def test_client(test_app):
    add_resources(test_app)
    with test_app.test_client() as client:
        yield client
        db.session.remove()
        db.drop_all()
