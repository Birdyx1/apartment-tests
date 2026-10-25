"""验证管理员认证 fixture 可被业务测试复用，查询结果必须属于登录账号。"""

from core.assertions import assert_response

import allure
import pytest

@pytest.mark.p1
@allure.title("管理员通过鉴权客户端查询本人信息")
def test_current_user_with_admin_token(
    admin_auth_api,
    login_payload,
):
    """登录作为 fixture 前置准备，测试本身只关心查询身份是否正确。"""
    response = admin_auth_api.current_user()

    body = assert_response(response)
    assert body["data"]["username"] == login_payload["username"]
