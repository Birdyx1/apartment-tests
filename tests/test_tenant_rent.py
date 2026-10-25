
from core.assertions import assert_response
from helpers.rent import (
    assert_bill_unchanged, assert_paid_bill, assert_paid_bill_list,
    confirm_mock_payment, start_mock_payment,
)
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
    body = assert_response(response)

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
    body = assert_response(response)

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
        tenant_lease_bill,
):
    """支付过程留在成功用例中，重复前置和结果断言由公共函数承接。"""
    bill = tenant_lease_bill
    payment = start_mock_payment(tenant_rent_api, bill["id"])
    confirm_mock_payment(tenant_rent_api, payment["paymentId"])
    assert_paid_bill(tenant_rent_api, bill, lease_payload["monthlyRent"])
    assert_paid_bill_list(tenant_rent_api, bill["id"], created_lease["tenantId"])





@pytest.mark.p1
@allure.title("租客不能再次支付已缴账单")
def test_tenant_cannot_pay_paid_bill(tenant_rent_api, paid_tenant_bill):
    """已缴账单作为前置，本用例只关注再次支付及原结果保持。"""
    bill = paid_tenant_bill["bill"]
    body = assert_response(
        tenant_rent_api.pay(bill["id"], {"channel": "ALIPAY"}), code=500,
    )
    assert body["message"] == "账单已缴"
    assert body.get("data") is None, "拒绝重复支付时不应返回新支付单"
    assert_bill_unchanged(tenant_rent_api, bill)


@pytest.mark.p1
@allure.title("重复确认模拟支付不改变原支付结果")
def test_tenant_mock_confirm_is_idempotent(tenant_rent_api, paid_tenant_bill):
    """重复确认原支付单，不能重写秒级缴费时间、流水或金额。"""
    bill = paid_tenant_bill["bill"]
    payment = paid_tenant_bill["payment"]
    sleep(1.1)
    confirm_mock_payment(tenant_rent_api, payment["paymentId"])
    assert_bill_unchanged(tenant_rent_api, bill)




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
    body = assert_response(response, http_status=http_status, code=business_code)
    # 参数校验消息含字段名前缀；业务拒绝消息应精确匹配。
    if http_status == 400:
        assert message in body["message"]
    else:
        assert body["message"] == message
    assert body.get("data") is None, "拒绝时不应返回支付单"
    assert_bill_unchanged(tenant_rent_api, tenant_lease_bill)


@pytest.mark.p0
@allure.title("租客不能查看其他租客账单，且本人列表不泄露账单")
def test_tenant_cannot_view_other_tenant_bill(
        tenant_lease_bill, tenant_rent_api,
        second_tenant_rent_api, created_second_tenant,
):
    assert tenant_lease_bill["tenantId"] != created_second_tenant["id"]
    response = second_tenant_rent_api.detail(tenant_lease_bill["id"])
    body = assert_response(response, code=500)
    assert body["message"] == "无权查看该账单"
    assert body.get("data") is None

    response = second_tenant_rent_api.list_bills()
    body = assert_response(response)
    bills = body["data"]
    assert isinstance(bills, list)
    assert tenant_lease_bill["id"] not in [bill["id"] for bill in bills]
    for bill in bills:
        assert bill["tenantId"] == created_second_tenant["id"]
    assert_bill_unchanged(tenant_rent_api, tenant_lease_bill)


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
    body = assert_response(response, code=500)
    assert body["message"] == "无权查看该账单"
    assert body.get("data") is None
    assert_bill_unchanged(tenant_rent_api, tenant_lease_bill)


@pytest.mark.p0
@allure.title("租客不能确认其他租客的模拟支付单")
def test_tenant_cannot_confirm_other_tenant_payment(
        tenant_lease_bill, tenant_rent_api,
        second_tenant_rent_api, created_second_tenant,
):
    assert tenant_lease_bill["tenantId"] != created_second_tenant["id"]
    # 先真实建立 A 的支付单，才能区分越权拒绝与“不存在”的拒绝。
    payment = start_mock_payment(tenant_rent_api, tenant_lease_bill["id"])
    body = assert_response(
        second_tenant_rent_api.mock_confirm(payment["paymentId"]), code=500,
    )
    assert body["message"] == "无权操作"
    assert body.get("data") is None
    assert_bill_unchanged(tenant_rent_api, tenant_lease_bill)
    # B 的失败请求不应妨碍 A 正常确认。
    confirm_mock_payment(tenant_rent_api, payment["paymentId"])
    assert_paid_bill(tenant_rent_api, tenant_lease_bill, tenant_lease_bill["amount"])
