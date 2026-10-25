"""租客资料及认证测试：管理员负责建档/清理，独立租客会话负责本人登录。"""

from core.assertions import assert_response

import pytest
import allure

def test_tenant_detail(created_tenant, admin_tenant_api):
    """管理员查询本次租客资料，检查 ID、姓名及性别，数据由 fixture 清理。"""
    tenant_id = created_tenant['id']
    response = admin_tenant_api.detail(tenant_id)
    body = assert_response(response)
    assert body['data']['id'] == tenant_id
    assert body['data']['name'] == created_tenant['name']
    assert body['data']['gender'] == created_tenant['gender']


@pytest.mark.p0
@allure.title("租客使用手机号和正确密码登录成功")
def test_tenant_login_success(tenant_auth_api,created_tenant):
    """使用手机号登录后，用同一令牌查询本人资料，核对返回身份。"""
    response = tenant_auth_api.login(
        {
            'account':created_tenant['phone'],
            'password':created_tenant['password'],
        }
    )
    body = assert_response(response)

    data = body.get('data')
    token = data['accessToken']
    assert isinstance(token,str)
    assert token.strip()
    assert data["tokenType"] == "Bearer"
    assert data["tenant"]["id"] == created_tenant["id"]
    assert data["tenant"]["name"] == created_tenant["name"]


    # token 非空不代表可用；实际携带它访问本人资料，再核对身份。
    # headers 仅影响当前请求，不修改客户端公共请求头。
    profile_response = tenant_auth_api.profile(
        headers = {
            "Authorization": f"Bearer {token}",
        }
    )

    body = assert_response(profile_response)
    assert body['data']['id'] == created_tenant['id']
    assert body['data']['name'] == created_tenant['name']

@pytest.mark.p1
@allure.title("租客使用错误密码登录被拒绝")
def test_tenant_login_wrong_password(tenant_auth_api,created_tenant):
    """真实存在的本次租客配错误密码，验证明确拒绝且不返回登录数据。"""
    response = tenant_auth_api.login(
        {
            'account':created_tenant['phone'],
            'password':'wrong_password',
        }
    )
    body = assert_response(response, code=500)
    assert body['message'] == "密码错误"
    assert body.get('data') is None
