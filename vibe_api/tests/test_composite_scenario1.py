import pytest
import logging
import os
import json
from vibe_api.app import create_app, add_resources
from vibe_api.db import db


@pytest.fixture(scope="module")
def test_client():
    app = create_app(is_test=True)
    add_resources(app)
    with app.test_client() as client:
        yield client
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="module")
def create_users(test_client):
    users_to_create = [
        {
            "name": "user0",
            "email": "user0@vibe.com",
        },
        {
            "name": "user1",
            "email": "user1@vibe.com",
            "age": 24,
        },
        {
            "name": "user2",
            "email": "user2@vibe.com",
            "gender": "male",
        },
        {
            "name": "user3",
            "email": "user3@vibe.com",
            "age": 32,
            "gender": "female",
        },
    ]

    user_ids = []
    for user in users_to_create:
        response = test_client.post('/user', json=user)
        json_data = response.get_json()
        logging.debug(json.dumps(json_data, indent=2))
        user_ids.append(json_data['id'])
        assert response.status_code == 201

    yield user_ids


@pytest.fixture(scope="module")
def create_follows(test_client, create_users):
    follows = [
        { "from": 0, "to": 1 },
        { "from": 0, "to": 2 },
        { "from": 0, "to": 3 },
        { "from": 1, "to": 0 },
        { "from": 2, "to": 0 },
        { "from": 2, "to": 3 },
        { "from": 3, "to": 2 },
    ]

    for follow in follows:
        response = test_client.post('/follow', json={
            "user_from": create_users[follow['from']],
            "user_to": create_users[follow['to']],
        })
        json_data = response.get_json()
        logging.debug(json.dumps(json_data, indent=2))
        assert response.status_code == 201


def test_get_users_via_api(test_client, create_users):
    for user_id in create_users:
        response = test_client.get(f'/user/{user_id}')
        json_data = response.get_json()
        logging.debug(json.dumps(json_data, indent=2))
        assert response.status_code == 200


def test_get_followers_of_a_user_via_api(test_client, create_users, create_follows):
    user = create_users[0]
    response = test_client.get(f'/followers/{user}')
    json_data = response.get_json()
    logging.debug(json.dumps(json_data, indent=2))
    assert len(json_data) == 2
    assert response.status_code == 200


def test_get_followings_of_a_user_via_api(test_client, create_users, create_follows):
    user = create_users[0]
    response = test_client.get(f'/followings/{user}')
    json_data = response.get_json()
    logging.debug(json.dumps(json_data, indent=2))
    assert len(json_data) == 3
    assert response.status_code == 200


@pytest.fixture(scope="module")
def create_post(test_client, create_users):
    logging.debug(f"Working Directory: {os.getcwd()}")
    media_paths = [
        "./test images/image0 for beach post.jpeg",
        "./test images/image1 for beach post.jpeg",
        "./test images/image2 for beach post.jpeg",]
    media = []
    files = []
    for media_path in media_paths:
        file = open(media_path, "rb")
        files.append(file)
        media.append((file, os.path.basename(media_path)))

    response = test_client.post('/post', data={
        'created_by': create_users[0],
        'caption': "Let's go to the beach!!!",
        "media": media,
        },
        content_type="multipart/form-data")
    json_data = response.get_json()
    logging.debug(json.dumps(json_data, indent=2))
    assert response.status_code == 201

    for file in files:
        file.close()

    yield json_data


def test_get_post(test_client, create_post):
    post_id = create_post['id']
    response = test_client.get(f'/post/{post_id}')
    json_data = response.get_json()
    logging.debug(json.dumps(json_data, indent=2))
    assert response.status_code == 200


def test_update_post(test_client, create_post):
    post_data = create_post
    media_paths = [
        "./test images/image3 for beach post.jpeg",
    ]
    media = []
    files = []
    for media_path in media_paths:
        file = open(media_path, "rb")
        files.append(file)
        media.append((file, os.path.basename(media_path)))

    media_order = [
        post_data['media'][0]['id'],
        os.path.basename(media_paths[0]),
        post_data['media'][1]['id'],
        ]
    
    request_data = {
        'caption': "Let's go to the beach!! would you join us?",
        'media_to_delete': [post_data['media'][2]['id']],
        "media": media,
        "media_order": media_order,
        }
    post_id = post_data['id']
    response = test_client.put(f'/post/{post_id}', data=request_data, content_type="multipart/form-data")
    json_data = response.get_json()
    logging.debug(json.dumps(json_data, indent=2))

    for file in files:
        file.close()

    assert response.status_code == 200
    assert len(json_data['media']) == 3
    assert json_data['media'][0]['id'] == post_data['media'][0]['id']
    assert json_data['media'][2]['id'] == post_data['media'][1]['id']


def test_delete_post(test_client, create_post):
    post_id = create_post['id']
    response = test_client.delete(f'/post/{post_id}')
    assert response.status_code == 204
    response = test_client.get(f'/post/{post_id}')
    json_data = response.get_json()
    logging.debug(json.dumps(json_data, indent=2))
    assert response.status_code == 404
