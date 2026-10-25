"""D04 专项回归：不同身份域即使数字 ID 相同，也不应互相下线。"""

from dataclasses import dataclass, field
from uuid import uuid4

import allure
import pytest
import requests

from apis.tenant_auth_api import TenantAuthApi
from apis.worker_auth_api import WorkerAuthApi
from core.api_client import ApiClient


@dataclass
class _Identity:
    id: int
    account: str
    password: str = field(repr=False)


@pytest.fixture
def same_id_identities(admin_tenant_api, admin_user_api, worker_role_id):
    """仅通过 API 准备同数字 ID 的两种身份，结束后清理所有中间账号。

    两张表独立自增，追加较小一侧的测试账号直到相等；不指定主键、
    不改自增值、不恢复历史账号。最多推进 100 次，避免无界建号。
    """
    cleanup_accounts = []

    def create_tenant():
        suffix = uuid4().hex[:12]
        payload = {
            "name": f"登录隔离租客-{suffix}",
            "gender": 1,
            "phone": f"199{uuid4().int % 100000000:08d}",
            "idCard": f"TEST{uuid4().hex[:14]}",
            "password": "Tenant123!",
        }
        response = admin_tenant_api.create(payload)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 200, body.get("message")
        tenant_id = body["data"]["id"]
        assert type(tenant_id) is int and tenant_id > 0
        cleanup_accounts.append((admin_tenant_api, tenant_id))
        return _Identity(tenant_id, payload["phone"], payload["password"])

    def create_worker():
        suffix = uuid4().hex[:12]
        payload = {
            "username": f"auto_isolation_{suffix}",
            "password": "Worker123!",
            "email": f"auto_isolation_{suffix}@example.com",
            "phone": f"199{uuid4().int % 100000000:08d}",
            "status": 1,
            "roleIds": [worker_role_id],
        }
        response = admin_user_api.create(payload)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 200, body.get("message")
        worker_id = body["data"]["id"]
        assert type(worker_id) is int and worker_id > 0
        cleanup_accounts.append((admin_user_api, worker_id))
        return _Identity(worker_id, payload["username"], payload["password"])

    try:
        tenant = create_tenant()
        worker = create_worker()
        for _ in range(100):
            if tenant.id == worker.id:
                break
            if tenant.id < worker.id:
                tenant = create_tenant()
            else:
                worker = create_worker()
        assert tenant.id == worker.id, "100 次内未准备出同数字 ID 的身份，请检查数据环境"
        # 仅记录数字 ID 和建号数量，不把密码或令牌写入报告。
        allure.attach(
            f"共同数字 ID：{tenant.id}\n本次创建账号数：{len(cleanup_accounts)}",
            name="身份冲突前置证据",
            attachment_type=allure.attachment_type.TEXT,
        )
        yield {"tenant": tenant, "worker": worker}
    finally:
        errors = []
        for api, account_id in reversed(cleanup_accounts):
            try:
                response = api.delete(account_id)
                if response.status_code != 200 or response.json().get("code") != 200:
                    errors.append(f"{type(api).__name__} 删除 {account_id} 失败")
            except Exception as exc:
                errors.append(f"{type(api).__name__} 删除 {account_id} 异常：{type(exc).__name__}")
        assert not errors, "；".join(errors)


@pytest.mark.p0
@allure.title("相同数字 ID 的租客与维修工登录状态应互相独立")
@pytest.mark.parametrize("first_kind", ["tenant", "worker"], ids=["tenant-first", "worker-first"])
def test_same_id_cross_role_sessions_stay_valid(
        same_id_identities, base_url, request_timeout, first_kind,
):
    """先验证两个身份各自能登录，再检查后登录者是否错误撤销先登录者。"""
    assert same_id_identities["tenant"].id == same_id_identities["worker"].id
    with requests.Session() as tenant_session, requests.Session() as worker_session:
        apis = {
            "tenant": TenantAuthApi(ApiClient(tenant_session, base_url, request_timeout)),
            "worker": WorkerAuthApi(ApiClient(worker_session, base_url, request_timeout)),
        }

        def login(kind):
            identity = same_id_identities[kind]
            account_field = "account" if kind == "tenant" else "username"
            response = apis[kind].login({
                account_field: identity.account,
                "password": identity.password,
            })
            assert response.status_code == 200
            body = response.json()
            assert body["code"] == 200, body.get("message")
            data = body["data"]
            identity_field = "tenant" if kind == "tenant" else "user"
            assert data[identity_field]["id"] == identity.id
            token = data["accessToken"]
            assert isinstance(token, str) and token.strip()
            apis[kind].client.session.headers.update({"Authorization": f"Bearer {token}"})

        def check_profile(kind, stage):
            response = apis[kind].profile()
            assert response.status_code == 200, (
                f"{stage}：{kind} 本人资料应可访问，实际 HTTP {response.status_code}；"
                f"响应：{response.text}"
            )
            body = response.json()
            assert body["code"] == 200, body.get("message")
            assert body["data"]["id"] == same_id_identities[kind].id

        second_kind = "worker" if first_kind == "tenant" else "tenant"
        login(first_kind)
        check_profile(first_kind, "另一角色登录前")
        login(second_kind)
        check_profile(second_kind, "第二个角色刚登录后")
        # 正确预期仍为 200；当前 D04 会让先登录的一方返回 401。
        check_profile(first_kind, "另一角色登录后")
