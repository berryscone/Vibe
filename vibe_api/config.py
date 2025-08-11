import os
from dotenv import load_dotenv


load_dotenv()

database_uri = os.getenv("DATABASE_URI")
if not database_uri:
    raise RuntimeError("DATABASE_URI not set in environment")

test_database_uri = os.getenv("TEST_DATABASE_URI")
if not test_database_uri:
    raise RuntimeError("TEST_DATABASE_URI not set in environment")


class ConfigProd:
    SQLALCHEMY_DATABASE_URI = database_uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    # SQLALCHEMY_RECORD_QUERIES = False

    
class ConfigTest:
    SQLALCHEMY_DATABASE_URI = test_database_uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    # SQLALCHEMY_RECORD_QUERIES = False