import allure
import pytest

@pytest.mark.p1
@allure.title("管理员通过鉴权客户端查询本人信息")
def test_current_user_with_admin_token(
    admin_auth_api,
    login_payload,
):
    response = admin_auth_api.current_user()

    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200
    assert body["data"]["username"] == login_payload["username"]