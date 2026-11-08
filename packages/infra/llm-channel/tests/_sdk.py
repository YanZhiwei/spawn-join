"""Real SDK exception fixtures for mapping tests."""

import anthropic
import httpx2
import openai


def _request() -> httpx2.Request:
    return httpx2.Request("GET", "https://api.example.com/v1/models")


def _response(status_code: int) -> httpx2.Response:
    return httpx2.Response(status_code, request=_request())


def openai_auth() -> Exception:
    return openai.AuthenticationError(
        "authentication failed",
        response=_response(401),
        body=None,
    )


def openai_status(status_code: int) -> Exception:
    return openai.APIStatusError(
        "status error",
        response=_response(status_code),
        body=None,
    )


def openai_not_found() -> Exception:
    return openai.NotFoundError(
        "not found",
        response=_response(404),
        body=None,
    )


def openai_timeout() -> Exception:
    return openai.APITimeoutError(_request())


def openai_connection() -> Exception:
    return openai.APIConnectionError(request=_request())


def openai_rate_limit() -> Exception:
    return openai.RateLimitError(
        "rate limited",
        response=_response(429),
        body=None,
    )


def openai_server() -> Exception:
    return openai.InternalServerError(
        "server error",
        response=_response(500),
        body=None,
    )


def openai_validation() -> Exception:
    return openai.APIResponseValidationError(_response(200), body=None)


def anthropic_auth() -> Exception:
    return anthropic.AuthenticationError(
        "authentication failed",
        response=_response(401),
        body=None,
    )


def anthropic_not_found() -> Exception:
    return anthropic.NotFoundError(
        "not found",
        response=_response(404),
        body=None,
    )
