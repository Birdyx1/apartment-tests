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
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200, body.get("message")

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
    assert profile_response.status_code == 200
    profile_body = profile_response.json()
    assert profile_body["code"] == 200, profile_body.get("message")

    profile = profile_body["data"]
    assert profile["id"] == created_worker["id"]
    assert profile["username"] == created_worker["username"]


@pytest.mark.p0
@allure.title("未携带令牌时不能查询维修工本人信息")
def test_worker_profile_without_token(worker_auth_api):
    """未携带令牌时不能查询维修工本人信息"""
    response = worker_auth_api.profile()
    assert response.status_code == 401

    body = response.json()
    assert body["code"] == 401
    assert body["message"] == "请先登录"
    assert body.get("data") is None

@pytest.mark.p1
@allure.title("携带无效格式令牌时不能查询维修工本人信息")
def test_worker_profile_invalid_token_format(worker_auth_api):
    """携带无效格式令牌时不能查询维修工本人信息"""
    response = worker_auth_api.profile(
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401

    body = response.json()
    assert body["code"] == 401
    assert body["message"] == "无效的token格式"
    assert body.get("data") is None
