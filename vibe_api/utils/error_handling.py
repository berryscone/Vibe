from http import HTTPStatus
from vibe_api.constants import InternalErrorCode


def make_error_response(int_error_code: InternalErrorCode, message: str, http_status: HTTPStatus):
    return {
        "error": message,
        "error_code": int_error_code.value,
        "error_text": int_error_code.text,
        "http_status": http_status.value,
        "message": message
        }, http_status.value
