
from core.assertions import assert_response
import pytest
import allure

@pytest.mark.p0
@allure.title("维修工使用正确账号密码登录成功")
def test_worker_login_success(worker_auth_api, created_worker):
    """维修工使用正确账号密码登录成功"""
    """查询角色 → 创建维修工 → 登录并核对身份 → 删除临时账号。"""
    response = worker_auth_api.login({
        "username": created_worker["username"],
        "password": created_worker["password"],
    })
    body = assert_response(response)

    data = body["data"]
    token = data["accessToken"]
    assert isinstance(token, str)
    assert token.strip(), "登录成功后令牌不能为空"

    user = data["user"]
    assert user["id"] == created_worker["id"]
    assert user["username"] == created_worker["username"]

    # 使用本次登录获得的令牌查询本人信息。
    profile_response = worker_auth_api.profile(
        headers={"Authorization": f"Bearer {token}"}
    )
    profile_body = assert_response(profile_response)

    profile = profile_body["data"]
    assert profile["id"] == created_worker["id"]
    assert profile["username"] == created_worker["username"]


@pytest.mark.p0
@allure.title("未携带令牌时不能查询维修工本人信息")
def test_worker_profile_without_token(worker_auth_api):
    """未携带令牌时不能查询维修工本人信息"""
    response = worker_auth_api.profile()
    body = assert_response(response, http_status=401, code=401)
    assert body["message"] == "请先登录"
    assert body.get("data") is None

@pytest.mark.p1
@allure.title("携带无效格式令牌时不能查询维修工本人信息")
def test_worker_profile_invalid_token_format(worker_auth_api):
    """携带无效格式令牌时不能查询维修工本人信息"""
    response = worker_auth_api.profile(
        headers={"Authorization": "Bearer invalid_token"}
    )
    body = assert_response(response, http_status=401, code=401)
    assert body["message"] == "无效的token格式"
    assert body.get("data") is None

@pytest.mark.p1
@allure.title("维修工使用错误密码登录时被拒绝")
def test_worker_login_wrong_password(worker_auth_api, created_worker):
    response = worker_auth_api.login({
        "username": created_worker["username"],
        "password": created_worker["password"] + "-wrong",
    })
    body = assert_response(response, code=500)
    assert body["message"] == "用户名或密码错误"
    assert body.get("data") is None


@pytest.mark.p1
@allure.title("管理员禁用维修工后该账号不能登录")
def test_disabled_worker_cannot_login(admin_user_api, worker_auth_api, created_worker):
    disable_response = admin_user_api.change_status(created_worker["id"], 0)
    assert_response(disable_response)

    try:
        login_response = worker_auth_api.login({
            "username": created_worker["username"],
            "password": created_worker["password"],
        })
        body = assert_response(login_response, code=500)
        assert body["message"] == "用户已被禁用"
        assert body.get("data") is None
    finally:
        enable_response = admin_user_api.change_status(created_worker["id"], 1)
        assert_response(enable_response)

    reenabled_login = assert_response(worker_auth_api.login({
        "username": created_worker["username"],
        "password": created_worker["password"],
    }))
    token = reenabled_login["data"]["accessToken"]
    assert isinstance(token, str) and token.strip(), "重新启用后应能登录并获取令牌"
