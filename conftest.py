
import pytest
import requests

from apis import lease_api
from apis.room_api import RoomApi
from apis.tenant_api import TenantAPI
from config import BASE_URL,REQUEST_TIMEOUT,ADMIN_USERNAME,ADMIN_PASSWORD
from core.api_client import ApiClient
from apis.auth_api import AuthApi
from uuid import uuid4
from apis.apartment_api import ApartmentApi
from apis.tenant_auth_api import TenantAuthApi
from apis.lease_api import LeaseApi
from datetime import datetime




@pytest.fixture
def base_url():
    return BASE_URL
@pytest.fixture
def request_timeout():
    return REQUEST_TIMEOUT
@pytest.fixture
def login_payload():
    return {
        "username":ADMIN_USERNAME,
        "password":ADMIN_PASSWORD,
        "roleType": "admin",
        "captchaId": "local-learning",
        "captchaCode": "2998"
    }

@pytest.fixture
def api_session():
    with requests.Session() as session:
        yield session

@pytest.fixture
def admin_client(api_client,auth_api,login_payload):
    response = auth_api.login(login_payload)

    assert response.status_code == 200

    body = response.json()

    assert body['code'] == 200,(
        f"管理员登录准备失败：{body.get('message')}"
    )

    token = body['data']['accessToken']

    assert isinstance(token, str),(
        f"accessToken 应为字符串"
    )

    assert token.strip(),(
        f"accessToken 不能为空"
    )

    api_client.session.headers.update({
        "Authorization": f"Bearer {token}"
    })

    return api_client


@pytest.fixture
def api_client(api_session,base_url,request_timeout):
    return ApiClient(
        session=api_session,
        base_url=base_url,
        timeout=request_timeout,
    )

@pytest.fixture
def auth_api(api_client):
    return AuthApi(api_client)

# 提供带管理员身份认证对象接口
@pytest.fixture
def admin_auth_api(admin_client):
    return AuthApi(admin_client)


@pytest.fixture
def created_apartment(admin_apartment_api):
    name = f"自动化公寓{uuid4().hex[:8]}"
    response = admin_apartment_api.create({
        "name": name
    })
    assert response.status_code == 200
    body = response.json()
    assert body['code'] == 200

    apartment_id = body['data']['id']
    assert isinstance(apartment_id, int)
    assert apartment_id > 0
    try:
        yield {
            "id": apartment_id,
            "name": name
        }
    finally:
        cleanup = admin_apartment_api.delete(apartment_id)
        assert cleanup.status_code == 200
        assert cleanup.json()['code'] == 200

        check = admin_apartment_api.detail(apartment_id)

        assert check.status_code == 200

        check_body = check.json()
        assert check_body["code"] == 400
        assert check_body["message"] == "公寓不存在"
        assert check_body.get("data") is None

@pytest.fixture
# 它使用已登录的管理员客户端，不会再单独登录一次。
def admin_apartment_api(admin_client):
    return ApartmentApi(admin_client)


@pytest.fixture
def created_room(admin_room_api,created_apartment):
    payload = {
        "apartmentId": created_apartment["id"],
        "roomNo": f"自动化房间-{uuid4().hex[:8]}",
        "floor": 1,
        "layout": "一室一厅",
        "area": 30,
        "status": 0,
    }
    response = admin_room_api.create(payload)
    assert response.status_code == 200
    body = response.json()
    assert body['code'] == 200
    room_id = body['data']['id']
    assert isinstance(room_id, int)
    assert room_id > 0
    try:
        yield {
            "id": room_id,
            "apartmentId": payload['apartmentId'],
            "roomNo": payload['roomNo'],
        }

    finally:
        cleanup = admin_room_api.delete(room_id)
        assert cleanup.status_code == 200
        assert cleanup.json()['code'] == 200

        check = admin_room_api.detail(room_id)
        assert check.status_code == 200
        check_body = check.json()
        assert check_body["code"] == 400
        assert check_body["message"] == "房间不存在"
        assert check_body.get("data") is None

@pytest.fixture
def admin_room_api(admin_client):
    return RoomApi(admin_client)

@pytest.fixture
def login_state(auth_api, login_payload):
    correct_payload = login_payload.copy()

    def restore():
        response = auth_api.login(correct_payload)

        assert response.status_code == 200

        body = response.json()
        assert body["code"] == 200, (
            f"恢复登录状态失败：{body.get('message')}"
        )

    restore()

    try:
        yield
    finally:
        restore()


@pytest.fixture
def admin_tenant_api(admin_client):
    return TenantAPI(admin_client)
# 对象	用途
# admin_tenant_api	管理员创建、查询、删除租客资料
# tenant_client	租客登录及后续租客操作
@pytest.fixture
def tenant_client(base_url,request_timeout):
    with requests.Session() as session:
        yield ApiClient(
            session=session,
            base_url=base_url,
            timeout=request_timeout
        )


@pytest.fixture
def created_tenant(admin_tenant_api):
    payload = {
        "name": f"自动化租客-{uuid4().hex[:8]}",
        "gender": 1,
        "phone": f"199{uuid4().int % 100000000:08d}",
        "idCard": f"TEST{uuid4().hex[:14]}",
        "password":"Tenant123!"
    }
    response = admin_tenant_api.create(payload)
    assert response.status_code == 200
    body = response.json()
    assert body['code'] == 200
    tenant_id = body['data']['id']
    assert isinstance(tenant_id, int)
    assert tenant_id > 0
    try:
        yield {
            "id": tenant_id,
            "name": payload['name'],
            "gender": payload['gender'],
            "phone": payload["phone"],
            "password": payload["password"],
        }
    finally:
        cleanup = admin_tenant_api.delete(tenant_id)
        assert cleanup.status_code == 200
        assert cleanup.json()['code'] == 200

# 这里使用独立的 tenant_client，不要传 admin_client。
@pytest.fixture
def tenant_auth_api(tenant_client):
    return TenantAuthApi(tenant_client)

@pytest.fixture
def admin_lease_api(admin_client):
    return LeaseApi(admin_client)

@pytest.fixture
def lease_payload(created_room, created_tenant):
    return {
        "tenantId": created_tenant["id"],
        "roomId": created_room["id"],
        "checkInTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "leaseMonths": 1,
        "deposit": 500,
        "monthlyRent": 1500,
        "rentDueDay": 1,
    }
@pytest.fixture
def created_lease(admin_lease_api,lease_payload,admin_room_api):
    response = admin_lease_api.create(lease_payload)
    assert response.status_code == 200

    body = response.json()
    assert body['code'] == 200,(
        f"创建入住关系失败：{body.get('message')}"
    )

    lease_id = body['data']['id']
    assert isinstance(lease_id, int)
    assert lease_id > 0

    try:
        yield {
            "id": lease_id,
            "tenantId": lease_payload['tenantId'],
            "roomId": lease_payload['roomId'],
        }
    finally:
        checkout = admin_lease_api.checkout({
            "leaseId": lease_id,
            "checkOutTime":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        assert checkout.status_code == 200
        checkout_body = checkout.json()

        assert checkout_body["code"] == 200, (
            f"退房失败：{checkout_body.get('message')}"
        )
        assert checkout_body["data"] is True

        room_response = admin_room_api.detail(lease_payload['roomId'])

        assert room_response.status_code == 200, (
            f"查询房间状态失败：预期 HTTP 200，实际为 {room_response.status_code}"
        )
        room_body = room_response.json()

        assert room_body["code"] == 200
        assert room_body["data"]["id"] == lease_payload["roomId"]
        assert room_body["data"]["status"] == 0

        # 退房操作是否真正更新了原来的入住记录。
        lease_response = admin_lease_api.page(
            params={
                "tenantId": lease_payload['tenantId'],
                "roomId": lease_payload['roomId'],
            }
        )
        assert lease_response.status_code == 200
        lease_body = lease_response.json()
        assert lease_body["code"] == 200

        records = lease_body['data']['records']
        matched = [
            item for item in records
            if item["id"] == lease_id
        ]

        assert len(matched) == 1 # 退房会保留历史。
        assert matched[0]["status"] == 1
        assert matched[0]["checkOutTime"], "退房后应记录退房时间"

