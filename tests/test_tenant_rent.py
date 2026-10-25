import allure
import pytest
from decimal import Decimal
from datetime import date
from time import sleep

@pytest.mark.p0
@allure.title("租客入住后可查询本人租约账单")
def test_tenant_can_view_lease_bill(
        created_lease,
        tenant_rent_api,
        lease_payload
):
    '''
    入住生成账单 → 列表数据与入住输入核对 → 用账单 ID 查询详情 → 核对详情数据。
    created_lease：办理入住，触发后端出账。
    tenant_rent_api：使用这名租客的身份查询账单。
    :param created_lease:
    :param tenant_rent_api:
    :return:
    '''
    response = tenant_rent_api.list_bills()
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")

    bills = body["data"]
    assert isinstance(bills, list)

    # 本人列表中的账单都应属于当前租客。
    for bill in bills:
        assert bill["tenantId"] == created_lease["tenantId"]

    # 精确查找本次入住生成的账单。
    matched = [
        bill for bill in bills
        if bill["leaseId"] == created_lease["id"]
    ]
    assert len(matched) == 1, "应查到本次入住对应的一张账单"

    bill = matched[0]
    assert isinstance(bill["id"], int)
    assert bill["id"] > 0
    assert bill["roomId"] == created_lease["roomId"]
    assert bill["tenantId"] == created_lease["tenantId"]

    # 账单金额应等于办理入住时填写的月租金。
    expected_amount = Decimal(str(lease_payload["monthlyRent"]))
    actual_amount = Decimal(str(bill["amount"]))
    assert actual_amount == expected_amount, "账单金额应与月租金一致"

    # 首张账单对应入住月份。
    expected_month = lease_payload["checkInTime"][:7]
    assert bill["billMonth"] == expected_month

    # 根据本次账单月份和缴租日，核对应缴日期。
    expected_due_date = date.fromisoformat(
        f"{expected_month}-{lease_payload['rentDueDay']:02d}"
    )
    due_date = date.fromisoformat(bill["dueDate"])
    assert due_date == expected_due_date

    # 应缴日期已过去则为逾期，否则为待缴。
    if due_date < date.today():
        expected_status = 2
    else:
        expected_status = 0

    assert bill["status"] == expected_status


    # 使用列表返回的账单 ID 查询详情。
    response = tenant_rent_api.detail(bill["id"])
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")

    bill_detail = body["data"]

    # 同一张账单的关键字段应保持一致。
    for field in (
        "id", "leaseId", "tenantId", "roomId",
        "billMonth", "dueDate", "status",
    ):
        assert bill_detail[field] == bill[field], (
            f"账单详情与列表中的 {field} 不一致"
        )

    assert Decimal(str(bill_detail["amount"])) == expected_amount



@pytest.mark.p0
@allure.title("租客模拟支付成功后账单变为已缴")
def test_tenant_mock_pay_bill_success(
        created_lease,
        tenant_rent_api,
        lease_payload,
):
    """

    # 取得账单 → 发起模拟支付 → 确认支付 → 查询账单已缴
    :param created_lease:
    :param tenant_rent_api:
    :param lease_payload:
    :return:
    """
    response = tenant_rent_api.list_bills()
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")

    bills = body["data"]
    assert isinstance(bills, list)

    matched = [
        bill for bill in bills
        if bill["leaseId"] == created_lease["id"]
    ]
    assert len(matched) == 1, "应找到本次入住生成的账单"

    bill = matched[0]
    bill_id = bill["id"]

    assert bill["tenantId"] == created_lease["tenantId"]
    assert bill["roomId"] == created_lease["roomId"]
    assert bill["status"] in (0, 2), "支付前账单应为待缴或逾期"

    payload = {"channel": "ALIPAY"}
    response = tenant_rent_api.pay(bill_id, payload)
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")
    payment = body['data']

    assert payment['mode'] == 'MOCK'
    assert payment["channel"] == payload["channel"]

    # 取得后续模拟确认需要的支付单 ID。
    payment_id = payment["paymentId"]
    assert isinstance(payment_id, int)
    assert payment_id > 0

    # 使用支付单 ID 确认模拟支付。
    response = tenant_rent_api.mock_confirm(payment_id)
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")
    assert body["data"] is True

    # 使用账单 ID 查询支付后的实际结果。
    response = tenant_rent_api.detail(bill_id)
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")

    paid_bill = body["data"]
    assert paid_bill["id"] == bill_id
    assert paid_bill["leaseId"] == created_lease["id"]
    assert paid_bill["tenantId"] == created_lease["tenantId"]
    assert paid_bill["roomId"] == created_lease["roomId"]

    assert paid_bill["status"] == 1
    assert paid_bill["payChannel"] == payload["channel"]
    assert paid_bill["paidTime"], "支付成功后应记录缴费时间"

    assert isinstance(paid_bill["payTradeNo"], str)
    assert paid_bill["payTradeNo"].startswith("MOCK_")

    assert Decimal(str(paid_bill["amount"])) == Decimal(
        str(lease_payload["monthlyRent"])
    )


    # 按已缴状态查询本人账单。
    response = tenant_rent_api.list_bills(params={"status": 1})
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")

    paid_bills = body["data"]
    assert isinstance(paid_bills, list)

    matched = [
        item for item in paid_bills
        if item["id"] == bill_id
    ]
    assert len(matched) == 1, "已缴列表应唯一包含本次支付的账单"

    for item in paid_bills:
        assert item["status"] == 1, "已缴列表只能返回已缴账单"
        assert item["tenantId"] == created_lease["tenantId"]





@pytest.mark.p1
@allure.title("租客不能再次支付已缴账单")
def test_tenant_cannot_pay_paid_bill(
        created_lease,
        tenant_rent_api,
        lease_payload,
):
    """

    # 取得账单 → 发起模拟支付 → 确认支付 → 查询账单已缴
    :param created_lease:
    :param tenant_rent_api:
    :param lease_payload:
    :return:
    """
    response = tenant_rent_api.list_bills()
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")

    bills = body["data"]
    assert isinstance(bills, list)

    matched = [
        bill for bill in bills
        if bill["leaseId"] == created_lease["id"]
    ]
    assert len(matched) == 1, "应找到本次入住生成的账单"

    bill = matched[0]
    bill_id = bill["id"]

    assert bill["tenantId"] == created_lease["tenantId"]
    assert bill["roomId"] == created_lease["roomId"]
    assert bill["status"] in (0, 2), "支付前账单应为待缴或逾期"

    payload = {"channel": "ALIPAY"}
    response = tenant_rent_api.pay(bill_id, payload)
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")
    payment = body['data']

    assert payment['mode'] == 'MOCK'
    assert payment["channel"] == payload["channel"]

    # 取得后续模拟确认需要的支付单 ID。
    payment_id = payment["paymentId"]
    assert isinstance(payment_id, int)
    assert payment_id > 0

    # 使用支付单 ID 确认模拟支付。
    response = tenant_rent_api.mock_confirm(payment_id)
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")
    assert body["data"] is True

    # 使用账单 ID 查询支付后的实际结果。
    response = tenant_rent_api.detail(bill_id)
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")

    paid_bill = body["data"]
    assert paid_bill["id"] == bill_id
    assert paid_bill["leaseId"] == created_lease["id"]
    assert paid_bill["tenantId"] == created_lease["tenantId"]
    assert paid_bill["roomId"] == created_lease["roomId"]

    assert paid_bill["status"] == 1
    assert paid_bill["payChannel"] == payload["channel"]
    assert paid_bill["paidTime"], "支付成功后应记录缴费时间"

    assert isinstance(paid_bill["payTradeNo"], str)
    assert paid_bill["payTradeNo"].startswith("MOCK_")

    assert Decimal(str(paid_bill["amount"])) == Decimal(
        str(lease_payload["monthlyRent"])
    )


    # 按已缴状态查询本人账单。
    response = tenant_rent_api.list_bills(params={"status": 1})
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")

    paid_bills = body["data"]
    assert isinstance(paid_bills, list)

    matched = [
        item for item in paid_bills
        if item["id"] == bill_id
    ]
    assert len(matched) == 1, "已缴列表应唯一包含本次支付的账单"

    for item in paid_bills:
        assert item["status"] == 1, "已缴列表只能返回已缴账单"
        assert item["tenantId"] == created_lease["tenantId"]

    # 首次支付已成功，再次为同一账单发起支付。
    response = tenant_rent_api.pay(bill_id, payload)
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 500
    assert body["message"] == "账单已缴"
    assert body.get("data") is None, "拒绝重复支付时不应返回新支付单"
    # 重复支付被拒绝后，再次查询账单。
    response = tenant_rent_api.detail(bill_id)
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")

    after_bill = body["data"]

    for field in (
        "id", "leaseId", "tenantId", "roomId", "status",
        "billMonth", "dueDate", "payChannel", "paidTime", "payTradeNo",
    ):
        assert after_bill[field] == paid_bill[field], (
            f"重复支付被拒绝后，{field} 不应改变"
        )

    assert Decimal(str(after_bill["amount"])) == Decimal(
        str(paid_bill["amount"])
    )


@pytest.mark.p1
@allure.title("重复确认模拟支付不改变原支付结果")
def test_tenant_mock_confirm_is_idempotent(
        created_lease,
        tenant_rent_api,
        lease_payload,
):
    """完成首次模拟支付，再确认同一支付单，核对支付结果不被重写。"""
    response = tenant_rent_api.list_bills()
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200, body.get("message")
    assert isinstance(body["data"], list)
    matched = [
        bill for bill in body["data"]
        if bill["leaseId"] == created_lease["id"]
    ]
    assert len(matched) == 1, "应找到本次入住的唯一账单"
    bill = matched[0]
    assert bill["tenantId"] == created_lease["tenantId"]
    assert bill["roomId"] == created_lease["roomId"]
    assert bill["status"] in (0, 2)
    bill_id = bill["id"]

    response = tenant_rent_api.pay(bill_id, {"channel": "ALIPAY"})
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200, body.get("message")
    payment = body["data"]
    assert payment["mode"] == "MOCK"
    assert payment["channel"] == "ALIPAY"
    payment_id = payment["paymentId"]
    assert type(payment_id) is int and payment_id > 0

    response = tenant_rent_api.mock_confirm(payment_id)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200, body.get("message")
    assert body["data"] is True

    response = tenant_rent_api.detail(bill_id)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200, body.get("message")
    before_bill = body["data"]
    assert before_bill["id"] == bill_id
    assert before_bill["leaseId"] == created_lease["id"]
    assert before_bill["tenantId"] == created_lease["tenantId"]
    assert before_bill["roomId"] == created_lease["roomId"]
    assert before_bill["status"] == 1
    assert before_bill["payChannel"] == "ALIPAY"
    assert before_bill["paidTime"], "首次支付应记录缴费时间"
    assert isinstance(before_bill["payTradeNo"], str)
    assert before_bill["payTradeNo"].startswith("MOCK_")
    assert Decimal(str(before_bill["amount"])) == Decimal(
        str(lease_payload["monthlyRent"])
    )

    # 接口时间精度为秒；跨过一秒，才能捕捉重复确认重写缴费时间的问题。
    sleep(1.1)
    response = tenant_rent_api.mock_confirm(payment_id)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200, body.get("message")
    assert body["data"] is True

    response = tenant_rent_api.detail(bill_id)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200, body.get("message")
    after_bill = body["data"]
    for field in (
        "id", "leaseId", "tenantId", "roomId", "status",
        "billMonth", "dueDate", "payChannel", "paidTime", "payTradeNo",
    ):
        assert after_bill[field] == before_bill[field], (
            f"重复确认后，{field} 不应改变"
        )
    assert Decimal(str(after_bill["amount"])) == Decimal(str(before_bill["amount"]))


def _assert_bill_unchanged(api, before_bill):
    """失败请求后重新查询，核对账单和原支付结果没有被修改。"""
    response = api.detail(before_bill["id"])
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200, body.get("message")
    after_bill = body["data"]
    for field in (
        "id", "leaseId", "tenantId", "roomId", "status", "billMonth", "dueDate",
    ):
        assert after_bill[field] == before_bill[field], f"失败请求不应修改 {field}"
    for field in ("paidTime", "payChannel", "payTradeNo"):
        assert after_bill.get(field) == before_bill.get(field), f"失败请求不应修改 {field}"
    assert Decimal(str(after_bill["amount"])) == Decimal(str(before_bill["amount"]))


@pytest.mark.p1
@allure.title("无效支付渠道被拒绝且账单保持不变")
@pytest.mark.parametrize(
    "payload,http_status,business_code,message",
    [
        pytest.param({}, 400, 400, "支付渠道不能为空", id="missing-channel"),
        pytest.param({"channel": None}, 400, 400, "支付渠道不能为空", id="null-channel"),
        pytest.param({"channel": ""}, 400, 400, "支付渠道不能为空", id="empty-channel"),
        pytest.param({"channel": " "}, 400, 400, "支付渠道不能为空", id="blank-channel"),
        pytest.param({"channel": "BANK"}, 200, 500, "不支持的支付渠道", id="unsupported-channel"),
    ],
)
def test_tenant_cannot_pay_with_invalid_channel(
        tenant_lease_bill, tenant_rent_api,
        payload, http_status, business_code, message,
):
    response = tenant_rent_api.pay(tenant_lease_bill["id"], payload)
    assert response.status_code == http_status
    body = response.json()
    assert body["code"] == business_code
    # 参数校验消息含字段名前缀；业务拒绝消息应精确匹配。
    if http_status == 400:
        assert message in body["message"]
    else:
        assert body["message"] == message
    assert body.get("data") is None, "拒绝时不应返回支付单"
    _assert_bill_unchanged(tenant_rent_api, tenant_lease_bill)


@pytest.mark.p0
@allure.title("租客不能查看其他租客账单，且本人列表不泄露账单")
def test_tenant_cannot_view_other_tenant_bill(
        tenant_lease_bill, tenant_rent_api,
        second_tenant_rent_api, created_second_tenant,
):
    assert tenant_lease_bill["tenantId"] != created_second_tenant["id"]
    response = second_tenant_rent_api.detail(tenant_lease_bill["id"])
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 500
    assert body["message"] == "无权查看该账单"
    assert body.get("data") is None

    response = second_tenant_rent_api.list_bills()
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200, body.get("message")
    bills = body["data"]
    assert isinstance(bills, list)
    assert tenant_lease_bill["id"] not in [bill["id"] for bill in bills]
    for bill in bills:
        assert bill["tenantId"] == created_second_tenant["id"]
    _assert_bill_unchanged(tenant_rent_api, tenant_lease_bill)


@pytest.mark.p0
@allure.title("租客不能为其他租客账单发起支付")
def test_tenant_cannot_pay_other_tenant_bill(
        tenant_lease_bill, tenant_rent_api,
        second_tenant_rent_api, created_second_tenant,
):
    assert tenant_lease_bill["tenantId"] != created_second_tenant["id"]
    response = second_tenant_rent_api.pay(
        tenant_lease_bill["id"], {"channel": "ALIPAY"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 500
    assert body["message"] == "无权查看该账单"
    assert body.get("data") is None
    _assert_bill_unchanged(tenant_rent_api, tenant_lease_bill)


@pytest.mark.p0
@allure.title("租客不能确认其他租客的模拟支付单")
def test_tenant_cannot_confirm_other_tenant_payment(
        tenant_lease_bill, tenant_rent_api,
        second_tenant_rent_api, created_second_tenant,
):
    assert tenant_lease_bill["tenantId"] != created_second_tenant["id"]
    bill_id = tenant_lease_bill["id"]
    # A 发起支付，暂不确认；B 必须使用这笔确实存在的支付单验证越权。
    response = tenant_rent_api.pay(bill_id, {"channel": "ALIPAY"})
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200, body.get("message")
    assert body["data"]["mode"] == "MOCK"
    assert body["data"]["channel"] == "ALIPAY"
    payment_id = body["data"]["paymentId"]
    assert type(payment_id) is int and payment_id > 0

    response = second_tenant_rent_api.mock_confirm(payment_id)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 500
    assert body["message"] == "无权操作"
    assert body.get("data") is None
    _assert_bill_unchanged(tenant_rent_api, tenant_lease_bill)

    # B 的失败请求不应妨碍 A 随后正常确认支付。
    response = tenant_rent_api.mock_confirm(payment_id)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200, body.get("message")
    assert body["data"] is True
    response = tenant_rent_api.detail(bill_id)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200, body.get("message")
    paid_bill = body["data"]
    for field in ("id", "leaseId", "tenantId", "roomId"):
        assert paid_bill[field] == tenant_lease_bill[field]
    assert paid_bill["status"] == 1
    assert paid_bill["payChannel"] == "ALIPAY"
    assert paid_bill["paidTime"]
    assert isinstance(paid_bill["payTradeNo"], str)
    assert paid_bill["payTradeNo"].startswith("MOCK_")
    assert Decimal(str(paid_bill["amount"])) == Decimal(str(tenant_lease_bill["amount"]))
