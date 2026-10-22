import pytest
import allure
from data_loader import load_login_cases

@pytest.mark.p0
@allure.title("管理员登录成功后可查询本人信息")
def test_admin_login(auth_api,login_payload):
    # 登录 → 提取令牌 → 设置请求头 → 查询用户 → 核对身份。
    response = auth_api.login(login_payload)

    assert response.status_code == 200, (
        f"预期 HTTP 200，实际为 {response.status_code}，响应：{response.text}"
    )

    body = response.json()

    assert body['code'] == 200,(
        f"登录失败：{body.get('message')}"
    )

    token = body['data']['accessToken']

    assert isinstance(token, str),(
        f"accessToken 应为字符串"
    )

    assert token.strip(),(
        f"accessToken 不能为空"
    )



    me_response = auth_api.current_user(
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert me_response.status_code == 200

    me_body = me_response.json()

    assert me_body.get("code") == 200,(
        f"获取用户信息失败：{me_body.get('message')}"
    )

    assert me_body['data']['username'] == login_payload['username']

@pytest.mark.p1
@allure.title("错误验证码登录应被拒绝")
def test_admin_login_wrong_captcha(auth_api,login_payload):
    login_payload["captchaId"] = "nonexistent-captcha-for-learning"
    login_payload["captchaCode"] = "0000"
    response = auth_api.login(login_payload)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 500
    assert body["message"] == "验证码错误或已过期"
    assert body.get("data") is None, "验证码校验失败不应返回登录数据"

@pytest.mark.p1
@allure.title("管理员使用错误或空密码登录应被拒绝")
@pytest.mark.parametrize(
    "case",
    load_login_cases(),
    ids = lambda x: x["case_id"]
)
def test_admin_login_invalid_password(auth_api, login_payload, case,login_state):
    login_payload["password"] = case["password"]

    response = auth_api.login(login_payload)

    assert response.status_code == case["expected_http"]

    body = response.json()
    assert body["code"] == case["expected_code"]
    assert case["expected_message"] in body["message"]
    assert body.get("data") is None

@pytest.mark.p0
@allure.title("未提供令牌时应拒绝查询用户信息")
def test_current_user_without_token(auth_api):
    response = auth_api.current_user()
    assert response.status_code == 200

    body = response.json()

    assert body["code"] == 500
    assert body["message"] == "未提供访问token"
    assert body.get("data") is None, "未登录不应返回用户数据"

@pytest.mark.p1
@allure.title("无效令牌时应拒绝查询用户信息")
def test_current_user_invalid_token(auth_api):
    response = auth_api.current_user(
        headers={
            "Authorization": "Bearer invalid-token"
        }
    )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 500
    assert body["message"] == "访问token无效或已过期"
    assert body.get("data") is None, "无效token不应返回用户数据"

