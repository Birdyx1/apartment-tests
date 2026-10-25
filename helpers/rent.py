"""账单测试公共步骤，保留金额、归属和支付结果的业务检查。"""

from decimal import Decimal

from core.assertions import assert_response, assert_true_response


def start_mock_payment(api, bill_id, channel="ALIPAY"):
    payment = assert_response(api.pay(bill_id, {"channel": channel}))["data"]
    assert payment["mode"] == "MOCK"
    assert payment["channel"] == channel
    assert type(payment["paymentId"]) is int and payment["paymentId"] > 0
    return payment


def confirm_mock_payment(api, payment_id):
    assert_true_response(api.mock_confirm(payment_id))


def assert_paid_bill(api, original_bill, expected_amount, channel="ALIPAY"):
    """核对真实详情，不能只依据确认接口成功就认定已缴。"""
    bill = assert_response(api.detail(original_bill["id"]))["data"]
    for field in ("id", "leaseId", "tenantId", "roomId"):
        assert bill[field] == original_bill[field], f"支付后 {field} 不应改变"
    assert bill["status"] == 1
    assert bill["payChannel"] == channel
    assert bill["paidTime"], "支付成功后应记录缴费时间"
    assert isinstance(bill["payTradeNo"], str)
    assert bill["payTradeNo"].startswith("MOCK_")
    assert Decimal(str(bill["amount"])) == Decimal(str(expected_amount))
    return bill


def assert_paid_bill_list(api, bill_id, tenant_id):
    bills = assert_response(api.list_bills(params={"status": 1}))["data"]
    assert isinstance(bills, list)
    matched = [bill for bill in bills if bill["id"] == bill_id]
    assert len(matched) == 1, "已缴列表应唯一包含本次支付的账单"
    for bill in bills:
        assert bill["status"] == 1, "已缴列表只能返回已缴账单"
        assert bill["tenantId"] == tenant_id


def assert_bill_unchanged(api, before_bill):
    """重新查询，检查拒绝或重复确认没有覆盖原支付结果。"""
    after_bill = assert_response(api.detail(before_bill["id"]))["data"]
    for field in (
        "id", "leaseId", "tenantId", "roomId", "status", "billMonth", "dueDate",
    ):
        assert after_bill[field] == before_bill[field], f"{field} 不应改变"
    for field in ("paidTime", "payChannel", "payTradeNo"):
        assert after_bill.get(field) == before_bill.get(field), f"{field} 不应改变"
    assert Decimal(str(after_bill["amount"])) == Decimal(str(before_bill["amount"]))
