"""全项目共享的测试准备与清理。
Pytest 根据测试形参自动寻找同名 fixture，无需在测试中 import 本文件。
所有 fixture 当前均使用默认 function 作用域；同一测试内同名依赖会复用，
不同测试重新准备。测试函数中的断言验证业务，fixture 中的断言验证准备/清理。
"""

from core.assertions import assert_response, assert_true_response
from helpers.accounts import managed_account
from helpers.rent import (
    assert_paid_bill, assert_paid_bill_list, confirm_mock_payment, start_mock_payment,
)
import json
import allure
from minio import Minio
import pytest
import requests
from pathlib import Path

from apis.admin_maintenance_api import AdminMaintenanceApi
from apis.room_api import RoomApi
from apis.tenant_api import TenantAPI
from apis.tenant_maintenance_api import TenantMaintenanceApi
from apis.tenant_rent_api import TenantRentApi
from apis.user_api import UserApi
from apis.worker_file_api import WorkerFileApi
from apis.worker_maintenance_api import WorkerMaintenanceApi
from core.api_client import ApiClient
from apis.auth_api import AuthApi
from uuid import uuid4
from apis.apartment_api import ApartmentApi
from apis.notice_api import NoticeApi
from apis.tenant_auth_api import TenantAuthApi
from apis.lease_api import LeaseApi
from datetime import datetime
from apis.tenant_room_api import TenantRoomApi
from apis.tenant_notice_api import TenantNoticeApi
from apis.worker_auth_api import WorkerAuthApi
from apis.role_api import RoleApi
from apis.menu_api import MenuApi
from apis.operation_log_api import OperationLogApi
from apis.dashboard_api import DashboardApi

from config import (
    BASE_URL,
    REQUEST_TIMEOUT,
    ADMIN_USERNAME,
    ADMIN_PASSWORD,
    MINIO_ENDPOINT,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    MINIO_BUCKET,
    MINIO_SECURE,
)

def _login_worker(auth_api, client, worker):
    """A/B 共用登录检查，但各自使用自己的客户端和账号。"""
    body = assert_response(auth_api.login({
        "username": worker["username"], "password": worker["password"],
    }))
    data = body["data"]
    assert data["user"]["id"] == worker["id"]
    assert data["user"]["username"] == worker["username"]
    token = data["accessToken"]
    assert isinstance(token, str) and token.strip(), "维修工令牌不能为空"
    client.session.headers.update({"Authorization": f"Bearer {token}"})
    return client


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

    body = assert_response(response)

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
def api_evidence():
    """每条测试创建一个容器，供该测试内的所有 ApiClient 共享。"""
    return []

@pytest.fixture
def api_client(api_session, base_url, request_timeout, api_evidence):
    """为普通 Session 加上基础地址和超时；本 fixture 本身不登录。"""
    return ApiClient(
        session=api_session,
        base_url=base_url,
        timeout=request_timeout,
        evidence_records=api_evidence,
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
    body = assert_response(response)

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
def created_apartment_pair(admin_apartment_api):
    """创建两套名称共享唯一前缀的公寓，供跨页场景使用并负责清理。"""
    name_prefix = f"分页测试{uuid4().hex[:8]}"
    apartments = []

    try:
        for index in range(2):
            name = f"{name_prefix}-{index + 1}"
            body = assert_response(admin_apartment_api.create({"name": name}))
            apartment_id = body["data"]["id"]
            assert isinstance(apartment_id, int) and apartment_id > 0
            apartments.append({"id": apartment_id, "name": name})

        yield {"namePrefix": name_prefix, "items": apartments}
    finally:
        cleanup_errors = []
        for apartment in reversed(apartments):
            apartment_id = apartment["id"]
            try:
                cleanup = admin_apartment_api.delete(apartment_id)
                assert cleanup.status_code == 200
                assert cleanup.json()["code"] == 200

                check = admin_apartment_api.detail(apartment_id)
                assert check.status_code == 200
                check_body = check.json()
                assert check_body["code"] == 400
                assert check_body["message"] == "公寓不存在"
                assert check_body.get("data") is None
            except Exception as exc:
                cleanup_errors.append(f"公寓 {apartment_id} 清理失败：{exc}")

        assert not cleanup_errors, "；".join(cleanup_errors)

@pytest.fixture
# 它使用已登录的管理员客户端，不会再单独登录一次。
def admin_apartment_api(admin_client):
    """提供管理员身份的公寓接口对象。"""
    return ApartmentApi(admin_client)


@pytest.fixture
def admin_notice_api(admin_client):
    """提供管理员身份的公告接口对象。"""
    return NoticeApi(admin_client)


@pytest.fixture
def created_notice(admin_notice_api, created_apartment):
    """创建一条本次测试专用草稿公告，结束后删除。"""
    title = f"自动化公告-{uuid4().hex[:8]}"
    content = f"自动化公告内容-{uuid4().hex[:8]}"
    payload = {
        "title": title,
        "content": content,
        "apartmentId": created_apartment["id"],
    }
    body = assert_response(admin_notice_api.create(payload))
    notice_id = body["data"]["id"]
    assert isinstance(notice_id, int) and notice_id > 0

    try:
        yield {
            "id": notice_id,
            "title": title,
            "content": content,
            "apartmentId": created_apartment["id"],
        }
    finally:
        assert_true_response(admin_notice_api.delete(notice_id))


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
    body = assert_response(response)
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

        body = assert_response(response)

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
def tenant_client(base_url, request_timeout, api_evidence):
    """创建另一套独立 Session，避免与管理员客户端共用 Authorization。
    此时尚未登录；with/yield 负责会话使用后的关闭。
    """
    with requests.Session() as session:
        yield ApiClient(
            session=session,
            base_url=base_url,
            timeout=request_timeout,
            evidence_records=api_evidence,
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
    with managed_account(admin_tenant_api, payload, ("name", "gender", "phone", "password")) as tenant:
        yield tenant

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
    body = assert_response(response)

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
    body = assert_response(response)
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


@pytest.fixture
def tenant_notice_api(logged_in_tenant_client):
    """提供已登录租客身份的公告查询接口对象。"""
    return TenantNoticeApi(logged_in_tenant_client)


@pytest.fixture
def tenant_maintenance_api(logged_in_tenant_client):
    """
    提供使用已登录租客身份创建维修记录的接口
    :param logged_in_tenant_client:
    :return:
    """
    return TenantMaintenanceApi(logged_in_tenant_client)

@pytest.fixture
def maintenance_payload():
    """提供每次测试独立的保修请求数据"""
    return {
        "title": f"自动化报修-{uuid4().hex[:8]}",
        "description": "卫生间水管漏水",
        "urgency": 1,
        "imageKeys": [],
    }


@pytest.fixture
def created_maintenance(
        maintenance_payload,
        tenant_maintenance_api,
        created_lease,
):    # yield 前：依赖created_lease保证已入住，然后创建报修，取得工单ID。
    """创建报修工单；结束后取消未结束工单，保留已完成或已取消记录。"""
    response = tenant_maintenance_api.create(maintenance_payload)
    body = assert_response(response)

    order_id = body['data']['id']
    assert isinstance(order_id, int)
    assert order_id > 0
    try:
        yield {
            "id": order_id,
            "tenantId": created_lease['tenantId'],
            "roomId": created_lease['roomId'],
        }
    finally:
        # 先检查当前状态
        detail_response = tenant_maintenance_api.detail(order_id)
        assert detail_response.status_code == 200
        detail_body = detail_response.json()
        assert detail_body["code"] == 200, (
            f"查询报修工单详情失败：{detail_body.get('message')}"
        )
        status = detail_body["data"]["status"]

        if status in (0, 1):
            # 尚未结束的工单，取消后再进行后续退房。
            response = tenant_maintenance_api.cancel(order_id)
            body = assert_true_response(response)
            expected_status = 3
        else:
            # 已完成或已取消的工单，保留其终态。
            assert status in (2, 3), f"工单状态异常：{status}"
            expected_status = status

        response = tenant_maintenance_api.detail(order_id)
        assert response.status_code == 200

        body = response.json()
        assert body["code"] == 200, body.get("message")
        assert body["data"]["status"] == expected_status



@pytest.fixture
def worker_client(base_url, request_timeout, api_evidence):
    """保存独立的会话、请求头，结束后关闭会话。"""
    with requests.Session() as session:
        yield ApiClient(
            session = session,
            base_url = base_url,
            timeout = request_timeout,
            evidence_records = api_evidence,
        )


@pytest.fixture
def worker_auth_api(worker_client):
    """提供维修工登录接口对象,使用这个客户端调用维修工认证接口。"""
    return WorkerAuthApi(worker_client)

@pytest.fixture
def admin_role_api(admin_client):
    """提供管理员身份的角色查询接口对象。"""
    return RoleApi(admin_client)


@pytest.fixture
def admin_menu_api(admin_client):
    """提供管理员身份的系统菜单查询接口对象。"""
    return MenuApi(admin_client)


@pytest.fixture
def worker_menu_api(logged_in_worker_client):
    """提供已登录维修工身份的系统菜单查询接口对象。"""
    return MenuApi(logged_in_worker_client)


@pytest.fixture
def admin_operation_log_api(admin_client):
    """提供管理员身份的操作日志查询接口对象。"""
    return OperationLogApi(admin_client)


@pytest.fixture
def worker_operation_log_api(logged_in_worker_client):
    """提供已登录维修工身份的操作日志查询接口对象。"""
    return OperationLogApi(logged_in_worker_client)


@pytest.fixture
def admin_dashboard_api(admin_client):
    """提供管理员身份的运营概览接口对象。"""
    return DashboardApi(admin_client)


@pytest.fixture
def worker_dashboard_api(logged_in_worker_client):
    """提供已登录维修工身份的运营概览接口对象。"""
    return DashboardApi(logged_in_worker_client)


@pytest.fixture
def worker_role_id(admin_role_api):
    """根据维修工角色编码，查询实际角色 ID。"""
    response = admin_role_api.enabled()
    body = assert_response(response)

    roles = body["data"]
    assert isinstance(roles, list)

    matched = [
        role for role in roles
        if role["roleCode"] == "MAINTENANCE_WORKER"
    ]
    assert len(matched) == 1, "应恰好存在一个启用的维修工角色"

    role = matched[0]
    assert role["status"] == 1

    role_id = role["id"]
    assert type(role_id) is int and role_id > 0
    return role_id

@pytest.fixture
def admin_user_api(admin_client):
    """提供管理员身份的用户维护接口对象。"""
    return UserApi(admin_client)


@pytest.fixture
def worker_user_api(logged_in_worker_client):
    """提供已登录维修工身份的用户维护接口对象。"""
    return UserApi(logged_in_worker_client)


@pytest.fixture
def worker_payload(worker_role_id):
    """提供每次测试独立的维修工账号数据。"""
    suffix = uuid4().hex[:8]
    return {
        "username": f"auto_worker_{suffix}",
        "password": "Worker123!",
        "email": f"auto_worker_{suffix}@example.com",
        "phone": f"199{uuid4().int % 100000000:08d}",
        "status": 1,
        "roleIds": [worker_role_id],
    }

@pytest.fixture
def created_worker(admin_user_api,worker_payload):
    """创建维修工 A；with 退出时自动通过管理员接口删除。"""
    with managed_account(admin_user_api, worker_payload, ("username", "password")) as worker:
        yield worker


@pytest.fixture
def logged_in_worker_client(
        worker_client,
        worker_auth_api,
        created_worker,
):
    """登录 A，并仅设置 A 的独立会话。"""
    return _login_worker(worker_auth_api, worker_client, created_worker)

@pytest.fixture
def worker_maintenance_api(logged_in_worker_client):
    """提供已登录维修工身份的工单接口对象。"""
    return WorkerMaintenanceApi(logged_in_worker_client)


@pytest.fixture
def worker_file_api(logged_in_worker_client):
    """提供已登录维修工身份的图片上传接口对象。"""
    return WorkerFileApi(logged_in_worker_client)

@pytest.fixture
def repair_image_path():
    """提供处理图片的本地路径，此处不上传文件。"""
    path = Path(__file__).resolve().parent / "data" / "repair.png"
    assert path.is_file(), f"测试图片不存在：{path}"
    return path


@pytest.fixture
def minio_client():
    """提供 MinIO 客户端，用于清理测试上传的图片。"""
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE,
    )

@pytest.fixture
def uploaded_repair_image(
        worker_file_api,
        repair_image_path,
        minio_client,
):
    """上传测试图片，并在测试结束后删除本次上传的对象。"""
    """
    它分三部分：
    - yield 前：上传图片，检查上传成功。
    - yield data：把 objectKey、url 提供给测试使用。
    - finally：即使测试断言失败，也会尝试删除本次上传的图片；删除失败会报告后置错误。
    """
    response = worker_file_api.upload_image(repair_image_path)
    body = assert_response(response)

    data = body["data"]
    object_key = data["objectKey"]
    assert isinstance(object_key, str)
    assert object_key.startswith("maintenance/")
    assert object_key.endswith(".png")

    try:
        yield data
    finally:
        minio_client.remove_object(MINIO_BUCKET, object_key)
@pytest.fixture
def second_worker_payload(worker_payload):
    """准备维修工 B 的独立账号数据。"""
    payload = worker_payload.copy()
    suffix = uuid4().hex[:8]

    payload["username"] = f"auto_worker_b_{suffix}"
    payload["email"] = f"auto_worker_b_{suffix}@example.com"
    payload["phone"] = f"199{uuid4().int % 100000000:08d}"

    return payload

@pytest.fixture
def created_second_worker(admin_user_api, second_worker_payload):
    """创建维修工 B，复用账号生命周期逻辑，数据仍与 A 独立。"""
    with managed_account(admin_user_api, second_worker_payload, ("username", "password")) as worker:
        yield worker

@pytest.fixture
def second_worker_client(base_url, request_timeout, api_evidence):
    """提供维修工 B 的独立会话，结束后关闭。"""
    with requests.Session() as session:
        yield ApiClient(
            session=session,
            base_url=base_url,
            timeout=request_timeout,
            evidence_records=api_evidence,
        )

@pytest.fixture
def logged_in_second_worker_client(
        second_worker_client,
        created_second_worker,
):
    """登录 B，并仅设置 B 的独立会话。"""
    return _login_worker(
        WorkerAuthApi(second_worker_client), second_worker_client, created_second_worker,
    )

@pytest.fixture
def second_worker_maintenance_api(logged_in_second_worker_client):
    """提供已登录维修工 B 身份的工单接口对象。"""
    return WorkerMaintenanceApi(logged_in_second_worker_client)


@pytest.fixture
def admin_maintenance_api(admin_client):
    """提供已登录管理员身份的工单接口对象。
        admin_client：提供管理员会话和令牌
      ↓
        AdminMaintenanceApi：封装派单接口
      ↓
        admin_maintenance_api：供测试调用
    """
    return AdminMaintenanceApi(admin_client)

@pytest.fixture
def tenant_rent_api(logged_in_tenant_client):
    """提供已登录租客身份的账单接口对象。
        logged_in_tenant_client：提供租客令牌
          ↓
        tenant_rent_api：使用该身份查询账单
    """
    return TenantRentApi(logged_in_tenant_client)


@pytest.fixture
def tenant_lease_bill(created_lease, tenant_rent_api):
    """取得本次入住的唯一账单；入住 fixture 负责后续退房。"""
    response = tenant_rent_api.list_bills()
    body = assert_response(response)
    assert isinstance(body["data"], list)
    matched = [
        bill for bill in body["data"]
        if bill["leaseId"] == created_lease["id"]
    ]
    assert len(matched) == 1, "应取得本次入住的唯一账单"
    bill = matched[0]
    assert type(bill["id"]) is int and bill["id"] > 0
    assert bill["tenantId"] == created_lease["tenantId"]
    assert bill["roomId"] == created_lease["roomId"]
    assert bill["status"] in (0, 2)
    return bill


@pytest.fixture
def created_second_tenant(admin_tenant_api):
    """创建租客 B，用于验证其他租客账单的访问权限，结束后删除。"""
    payload = {
        "name": f"自动化租客B-{uuid4().hex[:8]}",
        "gender": 1,
        "phone": f"199{uuid4().int % 100000000:08d}",
        "idCard": f"TEST{uuid4().hex[:14]}",
        "password": "Tenant123!",
    }
    with managed_account(admin_tenant_api, payload, ("phone", "password")) as tenant:
        yield tenant


@pytest.fixture
def second_tenant_rent_api(
        created_second_tenant, base_url, request_timeout, api_evidence
):
    """使用 B 的独立会话登录，避免覆盖租客 A 的令牌。"""
    with requests.Session() as session:
        client = ApiClient(
            session, base_url, request_timeout,
            evidence_records=api_evidence,
        )
        response = TenantAuthApi(client).login({
            "account": created_second_tenant["phone"],
            "password": created_second_tenant["password"],
        })
        body = assert_response(response)
        data = body["data"]
        assert data["tenant"]["id"] == created_second_tenant["id"]
        token = data["accessToken"]
        assert isinstance(token, str) and token.strip()
        session.headers.update({"Authorization": f"Bearer {token}"})
        yield TenantRentApi(client)


@pytest.fixture
def paid_tenant_bill(tenant_lease_bill, tenant_rent_api, lease_payload):
    """为重复支付/确认场景准备已缴账单，复用原入住与资源清理。"""
    payment = start_mock_payment(tenant_rent_api, tenant_lease_bill["id"])
    confirm_mock_payment(tenant_rent_api, payment["paymentId"])
    bill = assert_paid_bill(tenant_rent_api, tenant_lease_bill, lease_payload["monthlyRent"])
    assert_paid_bill_list(tenant_rent_api, bill["id"], bill["tenantId"])
    return {"bill": bill, "payment": payment}

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    # setup、测试执行或 teardown 任一阶段失败时，都尝试附加证据。
    if not report.failed:
        return

    records = getattr(item, "funcargs", {}).get("api_evidence", [])
    if not records:
        return

    allure.attach(
        json.dumps(records, ensure_ascii=False, indent=2, default=str),
        name=f"接口请求证据-{report.when}",
        attachment_type=allure.attachment_type.JSON,
    )
