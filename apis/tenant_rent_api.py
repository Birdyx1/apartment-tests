class TenantRentApi:
    """租客查询账单与支付的接口。"""

    def __init__(self, client):
        self.client = client

    def list_bills(self, params=None):
        """查询当前租客的账单，可按状态筛选。"""
        return self.client.request(
            "GET",
            "/tenant-app/rent/bills",
            params=params,
        )
    def detail(self, bill_id):
        """查询当前租客有权查看的账单详情。
        bill_id 使用列表返回的账单 ID。接口根据登录令牌校验租客身份，无须传 tenantId
        """
        return self.client.request(
            "GET",
            f"/tenant-app/rent/bills/{bill_id}",
        )
    def pay(self, bill_id, payload):
        """为指定账单发起支付，返回支付单信息。
        账单 ID
        账单 bill_id
         ↓ 发起支付
        支付单 paymentId
            ↓   模拟确认成功
        账单变为已缴
        """
        return self.client.request(
            "POST",
            f"/tenant-app/rent/bills/{bill_id}/pay",
            json=payload,
        )

    def mock_confirm(self, payment_id):
        """确认本地模拟支付，使用支付单 ID。
        发起支付后返回的支付单 ID
        """

        return self.client.request(
            "POST",
            f"/tenant-app/rent/payments/{payment_id}/mock-confirm",
        )