"""工单测试共用的关联和处理人断言，期望状态仍在用例中明确给出。"""


def assert_order_identity(order, source, *, status):
    assert order["id"] == source["id"]
    assert order["tenantId"] == source["tenantId"]
    assert order["roomId"] == source["roomId"]
    assert order["status"] == status


def assert_worker_assignment(order, worker_id):
    assert order["handlerId"] == worker_id
    assert order["assigneeId"] == worker_id
