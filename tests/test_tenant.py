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


@pytest.mark.p1
@allure.title("管理员分页查询租客时手机号和身份证号已脱敏")
def test_admin_tenant_page_masks_personal_data(admin_tenant_api, created_tenant):
    page = assert_response(
        admin_tenant_api.page(params={
            "current": 1,
            "size": 10,
            "phone": created_tenant["phone"],
        })
    )["data"]

    assert page["current"] == 1
    assert page["size"] == 10
    assert page["total"] == 1
    assert len(page["records"]) == 1
    tenant = page["records"][0]
    assert tenant["id"] == created_tenant["id"]
    assert tenant["name"] == created_tenant["name"]
    assert "*" in tenant["phone"]
    assert created_tenant["phone"] not in tenant["phone"]
    assert "*" in tenant["idCard"]
    assert created_tenant["idCard"] not in tenant["idCard"]


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


@pytest.mark.p1
@allure.title("管理员更新租客资料时不提供密码不会改变登录密码")
def test_admin_update_tenant_profile_keeps_password(
    admin_tenant_api, tenant_auth_api, created_tenant
):
    updated_name = f"{created_tenant['name']}-已更新"
    payload = {
        "name": updated_name,
        "gender": 2 if created_tenant["gender"] != 2 else 1,
        "phone": created_tenant["phone"],
        "idCard": created_tenant["idCard"],
    }

    assert_response(admin_tenant_api.update(created_tenant["id"], payload))

    tenant = assert_response(
        admin_tenant_api.detail(created_tenant["id"])
    )["data"]
    assert tenant["id"] == created_tenant["id"]
    assert tenant["name"] == updated_name
    assert tenant["gender"] == payload["gender"]

    # password 未出现在更新 DTO 中，原登录凭据应继续有效。
    login_body = assert_response(tenant_auth_api.login({
        "account": created_tenant["phone"],
        "password": created_tenant["password"],
    }))
    assert login_body["data"]["tenant"]["id"] == created_tenant["id"]
    assert login_body["data"]["tenant"]["name"] == updated_name


@pytest.mark.p1
@allure.title("管理员设置租客密码后新密码可登录且旧密码失效")
def test_admin_set_tenant_password(
    admin_tenant_api, tenant_auth_api, created_tenant
):
    new_password = "Tenant456!"
    assert_response(
        admin_tenant_api.set_password(created_tenant["id"], new_password)
    )

    old_login = tenant_auth_api.login({
        "account": created_tenant["phone"],
        "password": created_tenant["password"],
    })
    old_body = assert_response(old_login, code=500)
    assert old_body["message"] == "密码错误"
    assert old_body.get("data") is None

    new_body = assert_response(tenant_auth_api.login({
        "account": created_tenant["phone"],
        "password": new_password,
    }))
    assert new_body["data"]["tenant"]["id"] == created_tenant["id"]


@pytest.mark.p1
@allure.title("管理员重置租客密码后返回的默认密码可登录")
def test_admin_reset_tenant_password(
    admin_tenant_api, tenant_auth_api, created_tenant
):
    reset_body = assert_response(
        admin_tenant_api.reset_password(created_tenant["id"])
    )
    default_password = reset_body["data"]["defaultPassword"]
    assert default_password == created_tenant["phone"][-6:]

    old_body = assert_response(tenant_auth_api.login({
        "account": created_tenant["phone"],
        "password": created_tenant["password"],
    }), code=500)
    assert old_body["message"] == "密码错误"
    assert old_body.get("data") is None

    new_body = assert_response(tenant_auth_api.login({
        "account": created_tenant["phone"],
        "password": default_password,
    }))
    assert new_body["data"]["tenant"]["id"] == created_tenant["id"]


@pytest.mark.p1
@allure.title("有租客修改权限的其他管理员不能更新他人创建的租客")
def test_other_admin_cannot_update_tenant_owned_by_another_admin(
    admin_tenant_api, admin_operator_tenant_api, created_tenant
):
    payload = {
        "name": f"{created_tenant['name']}-越权尝试",
        "gender": created_tenant["gender"],
        "phone": created_tenant["phone"],
        "idCard": created_tenant["idCard"],
    }

    response = admin_operator_tenant_api.update(created_tenant["id"], payload)
    body = assert_response(response, code=403)
    assert body["message"] == "无权操作该租客"

    owner_record = assert_response(
        admin_tenant_api.detail(created_tenant["id"])
    )["data"]
    assert owner_record["name"] == created_tenant["name"]


@pytest.mark.p1
@allure.title("更新租客时不能使用其他租客已登记的身份证号")
def test_admin_cannot_update_tenant_with_duplicate_id_card(
    admin_tenant_api, created_tenant, created_second_tenant
):
    payload = {
        "name": f"{created_tenant['name']}-重复证件尝试",
        "gender": created_tenant["gender"],
        "phone": created_tenant["phone"],
        "idCard": created_second_tenant["idCard"],
    }

    response = admin_tenant_api.update(created_tenant["id"], payload)
    body = assert_response(response, code=400)
    assert body["message"] == "身份证号已存在"

    tenant = assert_response(
        admin_tenant_api.detail(created_tenant["id"])
    )["data"]
    assert tenant["id"] == created_tenant["id"]
    assert tenant["name"] == created_tenant["name"]
