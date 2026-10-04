import logging

from app.logging_config import add_request_id, request_id_var


def make_record() -> logging.LogRecord:
    return logging.LogRecord("app.test", logging.INFO, __file__, 1, "msg", None, None)


def test_add_request_id_outside_request_uses_dash() -> None:
    record = make_record()

    assert add_request_id(record) is True
    assert record.request_id == "-"


def test_add_request_id_uses_context_value() -> None:
    record = make_record()
    token = request_id_var.set("abc123")
    try:
        add_request_id(record)
    finally:
        request_id_var.reset(token)

    assert record.request_id == "abc123"
