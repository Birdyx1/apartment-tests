"""全项目共享的测试准备与清理。
Pytest 根据测试形参自动寻找同名 fixture，无需在测试中 import 本文件。
所有 fixture 当前均使用默认 function 作用域；同一测试内同名依赖会复用，
不同测试重新准备。测试函数中的断言验证业务，fixture 中的断言验证准备/清理。
"""


import pytest
import requests

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
from apis.tenant_room_api import TenantRoomApi



@pytest.fixture
def base_url():
    """把配置中的服务地址提供给依赖它的客户端 fixture。"""
    return BASE_URL
@pytest.fixture
def request_timeout():
    """提供默认请求超时；实际应用默认值的是 ApiClient.request。"""
    return REQUEST_TIMEOUT
@pytest.fixture
def login_payload():
    """每条测试获得一份新登录字典；2998 是本地项目的演示验证码绕过值。"""
    return {
        "username":ADMIN_USERNAME,
        "password":ADMIN_PASSWORD,
        "roleType": "admin",
        "captchaId": "local-learning",
        "captchaCode": "2998"
    }

@pytest.fixture
def api_session():
    """创建普通 Session；yield 交给测试使用，退出 with 时自动关闭连接资源。"""
    with requests.Session() as session:
        yield session

@pytest.fixture
def admin_client(api_client,auth_api,login_payload):
    """完成管理员登录，并给本次 api_client 设置 Bearer 请求头。
    返回的是同一个客户端；同一测试中 api_client 也会看到该请求头，
    因此不能把这两个形参当作两个独立身份。
    """
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

    # 同一测试中的 api_client 与 admin_client 指向同一客户端，并非两个独立会话。
    api_client.session.headers.update({
        "Authorization": f"Bearer {token}"
    })

    return api_client


@pytest.fixture
def api_client(api_session,base_url,request_timeout):
    """为普通 Session 加上基础地址和超时；本 fixture 本身不登录。"""
    return ApiClient(
        session=api_session,
        base_url=base_url,
        timeout=request_timeout,
    )

@pytest.fixture
def auth_api(api_client):
    """普通认证接口对象，用于登录请求和未授权场景。"""
    return AuthApi(api_client)

# 提供带管理员身份认证对象接口
@pytest.fixture
def admin_auth_api(admin_client):
    """用已登录管理员客户端构造认证接口对象，不再重复登录。"""
    return AuthApi(admin_client)


@pytest.fixture
def created_apartment(admin_apartment_api):
    """创建本次专用公寓并提供 id/name；结束后只删除本次 ID 并查询确认不可见。"""
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
    """提供管理员身份的公寓接口对象。"""
    return ApartmentApi(admin_client)


@pytest.fixture
def created_room(admin_room_api,created_apartment):
    """在本次新公寓中创建空置房间，提供房间 ID、所属公寓 ID 和房间号。
    finally 删除房间并确认不可查询，然后其依赖 created_apartment 才结束。
    """
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
    """提供管理员身份的房间接口对象。"""
    return RoomApi(admin_client)

@pytest.fixture
def login_state(auth_api, login_payload):
    """在密码失败场景前后正确登录，避免串行重复运行累积管理员失败次数。
    先复制正确密码，防止测试修改 login_payload 后清理也拿到错误密码。
    已锁定账号无法靠此 fixture 解锁；本方案不支持同账号并行执行。
    """
    # 测试稍后会覆盖原字典中的 password，恢复时必须使用修改前的副本。
    correct_payload = login_payload.copy()

    def restore():
        """用保存的正确凭据登录，成功后后端会清除此账号的失败次数。"""
        response = auth_api.login(correct_payload)

        assert response.status_code == 200

        body = response.json()
        assert body["code"] == 200, (
            f"恢复登录状态失败：{body.get('message')}"
        )

    # 正确登录清除失败计数；如果账号已经锁定，这一步会明确报错而不会绕过锁定。
    restore()

    try:
        yield
    finally:
        # 测试断言失败也要尝试恢复计数，不依赖另一条成功用例先执行。
        restore()


@pytest.fixture
def admin_tenant_api(admin_client):
    """提供管理员身份的租客资料接口对象，不代表租客本人身份。"""
    return TenantAPI(admin_client)
# 对象	用途
# admin_tenant_api	管理员创建、查询、删除租客资料
# tenant_client	租客登录及后续租客操作
@pytest.fixture
def tenant_client(base_url,request_timeout):
    """创建另一套独立 Session，避免与管理员客户端共用 Authorization。
    此时尚未登录；with/yield 负责会话使用后的关闭。
    """
    with requests.Session() as session:
        yield ApiClient(
            session=session,
            base_url=base_url,
            timeout=request_timeout
        )


@pytest.fixture
def created_tenant(admin_tenant_api):
    """创建独立租客及本地练习密码，供详情、租客登录和入住场景复用。
    TEST 前缀身份证号是模拟数据，不代表覆盖了真实身份证格式验证。
    结束后删除本次租客；不要将提供的密码、完整请求体写入日志。
    """
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
    """使用普通租客客户端封装登录/资料接口，不会自动提前登录。"""
    return TenantAuthApi(tenant_client)

@pytest.fixture
def admin_lease_api(admin_client):
    """提供管理员身份的入住接口对象；tenantId 是操作对象而非请求者。"""
    return LeaseApi(admin_client)

@pytest.fixture
def lease_payload(created_room, created_tenant):
    """关联同一次测试创建的租客和房间，并生成当前时间及租金字段。
    只组装数据，不办理入住；依赖 created_room 间接准备了公寓。
    """
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
    """入住后提供租约 ID 和关联 ID，测试结束时先退房，再检查两种状态恢复。
    退房会保留租约/账单历史，随后才结束房间、租客等依赖 fixture。
    所以这段清理验证的是业务恢复，不是物理清空所有历史数据。
    """
    # 真实入住会将房间置为在住，并触发后端账单生成；不是纯查询操作。
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
        # 退房必须先于房间/租客清理；此 fixture 依赖它们，所以 Pytest 先结束本 fixture。
        checkout = admin_lease_api.checkout({
            "leaseId": lease_id,
            "checkOutTime":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        assert checkout.status_code == 200
        checkout_body = checkout.json()

        assert checkout_body["code"] == 200, (
            f"退房失败：{checkout_body.get('message')}"
        )
        # checkout 是 Response，checkout_body 才是解析后的字典。
        assert checkout_body["data"] is True

        # 退房接口成功还不够，需要确认房间已经从 2（在住）回到 0（空置）。
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
        # 这里是租约状态：1 表示已退房，与房间的状态编号含义不同。
        assert matched[0]["status"] == 1
        assert matched[0]["checkOutTime"], "退房后应记录退房时间"

# 已登录租客身份：只有依赖本 fixture 的测试才会提前登录。
@pytest.fixture
def logged_in_tenant_client(
        tenant_client,tenant_auth_api,created_tenant
):
    """用本次创建的租客登录并设置令牌，返回独立的已登录租客客户端。
    与 admin_client 不共用 Session；未授权测试不要依赖本 fixture。
    """
    response = tenant_auth_api.login({
        "account": created_tenant["phone"],
        "password": created_tenant["password"],
    })
    assert response.status_code == 200
    body = response.json()
    assert body['code'] == 200
    data = body['data']
    assert data['tenant']['id'] == created_tenant['id']

    token = data['accessToken']
    assert token.strip()
    assert isinstance(token, str)
    tenant_client.session.headers.update({
        "Authorization": f"Bearer {token}"
    })
    return tenant_client

@pytest.fixture
def tenant_room_api(logged_in_tenant_client):
    """为“我的房间”接口提供已登录租客身份，供后续业务测试使用。"""
    return TenantRoomApi(logged_in_tenant_client)
