"""统一临时账号的创建/删除，身份、会话和业务操作仍由 fixture 决定。"""

from contextlib import contextmanager

from core.assertions import assert_response


@contextmanager
def managed_account(api, payload, fields):
    """创建账号并提供指定字段；离开 with 时删除本次账号。"""
    body = assert_response(api.create(payload))
    account_id = body["data"]["id"]
    assert isinstance(account_id, int) and account_id > 0
    try:
        yield {"id": account_id, **{name: payload[name] for name in fields}}
    finally:
        assert_response(api.delete(account_id))
