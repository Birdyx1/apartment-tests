import pytest
import allure

def test_tenant_detail(created_tenant, admin_tenant_api):
    tenant_id = created_tenant['id']
    response = admin_tenant_api.detail(tenant_id)
    assert response.status_code == 200
    body = response.json()
    assert body['code'] == 200
    assert body['data']['id'] == tenant_id
    assert body['data']['name'] == created_tenant['name']
    assert body['data']['gender'] == created_tenant['gender']


@pytest.mark.p0
@allure.title("租客使用手机号和正确密码登录成功")
def test_tenant_login_success(tenant_auth_api,created_tenant):
    response = tenant_auth_api.login(
        {
            'account':created_tenant['phone'],
            'password':created_tenant['password'],
        }
    )
    assert response.status_code == 200
    body = response.json()

    assert body['code'] == 200,(
        f"租客登录失败：{body.get('message')}"
    )

    data = body.get('data')
    token = data['accessToken']
    assert isinstance(token,str)
    assert token.strip()
    assert data["tokenType"] == "Bearer"
    assert data["tenant"]["id"] == created_tenant["id"]
    assert data["tenant"]["name"] == created_tenant["name"]


    profile_response = tenant_auth_api.profile(
        headers = {
            "Authorization": f"Bearer {token}",
        }
    )

    assert profile_response.status_code == 200
    body = profile_response.json()
    assert body['code'] == 200
    assert body['data']['id'] == created_tenant['id']
    assert body['data']['name'] == created_tenant['name']

@pytest.mark.p1
@allure.title("租客使用错误密码登录被拒绝")
def test_tenant_login_wrong_password(tenant_auth_api,created_tenant):
    response = tenant_auth_api.login(
        {
            'account':created_tenant['phone'],
            'password':'wrong_password',
        }
    )
    assert response.status_code == 200
    body = response.json()
    assert body['code'] == 500
    assert body['message'] == "密码错误"
    assert body.get('data') is None