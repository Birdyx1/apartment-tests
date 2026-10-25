
from core.assertions import assert_response, assert_true_response
from helpers.maintenance import assert_order_identity, assert_worker_assignment
import pytest
import allure

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

@pytest.mark.p1
@allure.title("新维修工的本人已接工单列表为空")
def test_new_worker_has_no_mine_orders(worker_maintenance_api):
    """创建账号 → 登录 → 查询 → 结束后删除账号"""
    response = worker_maintenance_api.list(
        params={"tab": "mine"}
    )
    body = assert_response(response)

    orders = body["data"]
    assert isinstance(orders, list)
    assert orders == [], "新维修工尚未接单，本人列表应为空"

@pytest.mark.p0
@allure.title("租客创建报修后维修工待接列表包含该工单")
def test_tenant_order_visible_in_worker_todo(
        created_maintenance,
        worker_maintenance_api,
        maintenance_payload,
):
    """创建报修后，维修工待接列表应包含该工单"""
    """三个 fixture 分别准备：租客的报修工单、已登录维修工接口、创建时的原始数据。"""
    response = worker_maintenance_api.list(
        params = {"tab": "todo"}
    )
    body = assert_response(response)

    orders = body['data']
    assert isinstance(orders, list)

    matched = [
        item for item in orders
        if item["id"] == created_maintenance["id"]
    ]

    assert len(matched) == 1, "待接列表应唯一包含本次创建的工单"

    order = matched[0]
    assert order["tenantId"] == created_maintenance["tenantId"]
    assert order["roomId"] == created_maintenance["roomId"]
    assert order["title"] == maintenance_payload["title"]
    assert order["status"] == 0

@pytest.mark.p0
@allure.title("维修工抢单成功后工单进入处理中")
def test_worker_grab_order_success(
        created_maintenance,
        worker_maintenance_api,
        created_worker,
):
    order_id = created_maintenance["id"]

    response = worker_maintenance_api.grab(order_id)
    body = assert_true_response(response)

    # 查询详情，确认状态和处理人实际更新。
    response = worker_maintenance_api.detail(order_id)
    body = assert_response(response)

    order = body["data"]
    assert_order_identity(order, created_maintenance, status=1)
    assert_worker_assignment(order, created_worker['id'])

    # 抢单后，工单应进入当前维修工的本人列表。
    response = worker_maintenance_api.list(params={"tab": "mine"})
    body = assert_response(response)

    orders = body["data"]
    assert isinstance(orders, list)

    matched = [
        item for item in orders
        if item["id"] == order_id
    ]
    assert len(matched) == 1, "本人列表应唯一包含本次抢到的工单"

    mine_order = matched[0]
    assert mine_order["status"] == 1
    assert mine_order["handlerId"] == created_worker["id"]
    # 已被抢取的工单，不应继续出现在待接列表。
    response = worker_maintenance_api.list(params={"tab": "todo"})
    body = assert_response(response)

    orders = body["data"]
    assert isinstance(orders, list)

    order_ids = [item["id"] for item in orders]
    assert order_id not in order_ids, "抢单成功后，该工单应从待接列表移除"

# 同一维修工不能重复抢取已进入处理中的工单
@pytest.mark.p1
@allure.title("维修工不能重复抢取处理中的工单")
def test_worker_cannot_grab_order_twice(
        created_maintenance,
        worker_maintenance_api,
        created_worker,
):
    order_id = created_maintenance["id"]
    # 第一次抢单成功，让工单进入处理中。
    response = worker_maintenance_api.grab(order_id)
    body = assert_true_response(response)

    # 对同一工单再次发起抢单，应被拒绝。
    response = worker_maintenance_api.grab(order_id)
    body = assert_response(response, code=500)
    assert body["message"] == "仅待处理工单可抢单"

    # 重复抢单失败后，原来的状态和归属应保持不变。
    response = worker_maintenance_api.detail(order_id)
    body = assert_response(response)

    order = body["data"]
    assert_order_identity(order, created_maintenance, status=1)
    assert_worker_assignment(order, created_worker['id'])



@pytest.mark.p1
@allure.title("维修工未填写处理备注时不能完成工单")
def test_worker_cannot_complete_without_remark(
        created_maintenance,
        worker_maintenance_api,
        created_worker,
):
    order_id = created_maintenance["id"]
    # 先抢单，使工单进入处理中
    response = worker_maintenance_api.grab(order_id)
    body = assert_true_response(response)

    payload = {
        "handlerRemark":"",
        "imageKeys":[]
    }
    response = worker_maintenance_api.complete(order_id, payload)
    body = assert_response(response, code=400)
    assert body["message"] == "请填写处理备注"

    # 完工被拒绝后，工单状态和归属应保持不变。
    response = worker_maintenance_api.detail(order_id)
    body = assert_response(response)

    order = body["data"]
    assert_order_identity(order, created_maintenance, status=1)
    assert_worker_assignment(order, created_worker['id'])

@pytest.mark.p1
@allure.title("维修工未上传处理图片时不能完成工单")
def test_worker_cannot_complete_without_images(
        created_maintenance,
        worker_maintenance_api,
        created_worker,
):
    order_id = created_maintenance["id"]
    # 先抢单，使工单进入处理中
    response = worker_maintenance_api.grab(order_id)
    body = assert_true_response(response)

    payload = {
        "handlerRemark": "已更换漏水管道，检查无渗漏",
        "imageKeys": [],
    }
    response = worker_maintenance_api.complete(order_id, payload)
    body = assert_response(response, code=500)
    assert body["message"] == "请至少上传一张处理图片"
    # 完工被拒绝后，工单状态和归属应保持不变。
    response = worker_maintenance_api.detail(order_id)
    body = assert_response(response)

    order = body["data"]
    assert_order_identity(order, created_maintenance, status=1)
    assert_worker_assignment(order, created_worker['id'])


@pytest.mark.p0
@allure.title("维修工提交处理备注和图片后完成工单")
def test_worker_complete_order_success(
        created_maintenance,
        worker_maintenance_api,
        uploaded_repair_image,
        created_worker,
        tenant_maintenance_api,
):
    order_id = created_maintenance["id"]
    response = worker_maintenance_api.grab(order_id)
    body = assert_true_response(response)

    # 上传真实图片，取得完工请求所需图片Key。
    # fixture 已上传图片，并负责测试结束后的清理。
    object_key = uploaded_repair_image["objectKey"]

    payload = {
        "handlerRemark":"已更换漏水管道，检查无渗漏",
        "imageKeys":[object_key]
    }
    response = worker_maintenance_api.complete(order_id, payload)
    body = assert_true_response(response)
    # 查询详情，确认工单真正完成，处理结果正确保存。
    response = worker_maintenance_api.detail(order_id)
    body = assert_response(response)

    order = body["data"]
    assert_order_identity(order, created_maintenance, status=2)
    assert_worker_assignment(order, created_worker['id'])

    assert order["handlerRemark"] == payload["handlerRemark"]
    assert order["handleTime"], "完成工单后应记录处理时间"


    # 从申请租客的视角，验证同一工单的完工结果。

    response = tenant_maintenance_api.detail(order_id)
    body = assert_response(response)

    tenant_order = body["data"]
    assert tenant_order["id"] == order_id
    assert tenant_order["status"] == 2
    assert tenant_order["handlerId"] == created_worker["id"]
    assert tenant_order["handlerRemark"] == payload["handlerRemark"]

    # 查询本人已完成的工单。
    """
    tab="mine" 查询本人接过的工单，status=2 筛选其中已完成的工单
    """
    response = worker_maintenance_api.list(
        params={"tab": "mine", "status": 2},
    )
    body = assert_response(response)

    orders = body['data']
    assert isinstance(orders,list)
    matched = [
        item for item in orders
        if item["id"] == order_id
    ]
    assert len(matched) == 1, "已完成列表应唯一包含本次工单"

    completed_order = matched[0]
    assert completed_order["status"] == 2
    assert completed_order["handlerId"] == created_worker["id"]


@pytest.mark.p1
@allure.title("已完成工单不能再次完工")
def test_worker_cannot_complete_order_twice(
        created_maintenance,
        worker_maintenance_api,
        uploaded_repair_image,
        created_worker,
):
    """
    已完成的工单不能再次完工，原处理结果不能被覆盖
    :param created_maintenance:
    :param worker_maintenance_api:
    :param uploaded_repair_image:
    :param created_worker:
    :param tenant_maintenance_api:
    :return:
    """
    order_id = created_maintenance["id"]
    response = worker_maintenance_api.grab(order_id)
    body = assert_true_response(response)

    # 上传真实图片，取得完工请求所需图片Key。
    # fixture 已上传图片，并负责测试结束后的清理。
    object_key = uploaded_repair_image["objectKey"]

    payload = {
        "handlerRemark":"已更换漏水管道，检查无渗漏",
        "imageKeys":[object_key]
    }
    response = worker_maintenance_api.complete(order_id, payload)
    body = assert_true_response(response)
    # 查询详情，确认工单真正完成，处理结果正确保存。
    response = worker_maintenance_api.detail(order_id)
    body = assert_response(response)

    order = body["data"]
    assert_order_identity(order, created_maintenance, status=2)
    assert_worker_assignment(order, created_worker['id'])

    assert order["handlerRemark"] == payload["handlerRemark"]
    assert order["handleTime"], "完成工单后应记录处理时间"

    before_order = order.copy()
    # 使用不同备注再次提交，尝试覆盖原处理结果。
    retry_payload = {
        "handlerRemark": "第二次提交，尝试修改处理结果",
        "imageKeys": [object_key],
    }
    response = worker_maintenance_api.complete(order_id, retry_payload)
    body = assert_response(response, code=500)
    assert body["message"] == "仅处理中工单可完成"

    # 被拒绝后，重新查询并核对原数据。
    response = worker_maintenance_api.detail(order_id)
    body = assert_response(response)

    after_order = body["data"]
    for field in (
            "id", "status", "handlerId", "assigneeId",
            "tenantId", "roomId", "handlerRemark", "handleTime",
    ):
        assert after_order[field] == before_order[field], (
            f"重复完工被拒绝后，{field} 不应改变"
        )

@pytest.mark.p1
@allure.title("维修工不能抢取已取消的工单")
def test_worker_cannot_grab_cancelled_order(
        created_maintenance,
        tenant_maintenance_api,
        worker_maintenance_api,
):
    order_id = created_maintenance["id"]
    # 申请租客先取消工单。
    response = tenant_maintenance_api.cancel(order_id)
    body = assert_true_response(response)

    # 维修工尝试抢取已取消的工单，应被拒绝。
    response = worker_maintenance_api.grab(order_id)
    body = assert_response(response, code=500)
    assert body["message"] == "仅待处理工单可抢单"
    """
    抢单失败后，工单仍保持已取消
    """

    response = tenant_maintenance_api.detail(order_id)
    body = assert_response(response)
    order = body["data"]
    assert_order_identity(order, created_maintenance, status=3)

"""
待处理工单不能跳过抢单，直接完工
"""
@pytest.mark.p1
@allure.title("待处理工单不能直接完工")
def test_worker_cannot_complete_pending_order(
        created_maintenance,
        worker_maintenance_api,
        uploaded_repair_image,
):
    order_id = created_maintenance["id"]

    # 提供有效备注和图片，但不抢单，工单仍为待处理。
    payload = {
        "handlerRemark": "尝试跳过抢单直接完工",
        "imageKeys": [uploaded_repair_image["objectKey"]],
    }
    response = worker_maintenance_api.complete(order_id, payload)
    body = assert_response(response, code=500)
    assert body["message"] == "仅处理中工单可完成"
    # 完工失败后，工单仍应保持待处理。
    response = worker_maintenance_api.detail(order_id)
    body = assert_response(response)

    order = body["data"]
    assert_order_identity(order, created_maintenance, status=0)



"""
已取消工单不能跳过抢单，直接完工
"""
@pytest.mark.p1
@allure.title("已取消工单不能直接完工")
def test_worker_cannot_complete_cancelled_order(
        created_maintenance,
        worker_maintenance_api,
        uploaded_repair_image,
        tenant_maintenance_api,
):
    order_id = created_maintenance["id"]
    response = tenant_maintenance_api.cancel(order_id)
    body = assert_true_response(response)
    # 提供有效备注和图片，但不抢单，工单仍为待处理。
    payload = {
        "handlerRemark": "尝试完成已取消的工单",
        "imageKeys": [uploaded_repair_image["objectKey"]],
    }
    response = worker_maintenance_api.complete(order_id, payload)
    body = assert_response(response, code=500)
    assert body["message"] == "仅处理中工单可完成"
    # 完工失败后，工单仍应保持待处理。
    response = tenant_maintenance_api.detail(order_id)
    body = assert_response(response)

    order = body["data"]
    assert_order_identity(order, created_maintenance, status=3)

@pytest.mark.p0
@allure.title("维修工不能完成其他维修工接取的工单")
def test_worker_cannot_complete_other_worker_order(
        created_maintenance,
        worker_maintenance_api,
        second_worker_maintenance_api,
        uploaded_repair_image,
        created_worker,
        created_second_worker,
):
    order_id = created_maintenance["id"]
    assert created_worker["id"] != created_second_worker["id"]

    # A 抢单，使工单进入处理中。
    response = worker_maintenance_api.grab(order_id)
    body = assert_true_response(response)

    # B 尝试完成 A 的工单。
    payload = {
        "handlerRemark": "维修工 B 尝试完成 A 的工单",
        "imageKeys": [uploaded_repair_image["objectKey"]],
    }
    response = second_worker_maintenance_api.complete(order_id, payload)
    body = assert_response(response, code=500)
    assert body["message"] == "只能完成自己接的工单"

    # B 完工失败后，通过 A 查询工单。
    response = worker_maintenance_api.detail(order_id)
    body = assert_response(response)

    order = body["data"]
    assert_order_identity(order, created_maintenance, status=1)
    assert_worker_assignment(order, created_worker['id'])


@pytest.mark.p0
@allure.title("维修工的工单详情与本人列表按处理人隔离")
def test_worker_cannot_view_other_worker_order(
        created_maintenance,
        worker_maintenance_api,
        second_worker_maintenance_api,
        created_worker,
        created_second_worker
):
    order_id = created_maintenance["id"]
    assert created_worker["id"] != created_second_worker["id"]

    # A 抢单。
    response = worker_maintenance_api.grab(order_id)
    body = assert_true_response(response)

    # B 尝试读取 A 的处理中工单。
    response = second_worker_maintenance_api.detail(order_id)
    body = assert_response(response, code=500)
    assert body["message"] == "无权查看该工单"
    assert body.get("data") is None, "拒绝访问时不应返回工单详情"

    # B 的“本人列表”也不能出现 A 的工单。
    response = second_worker_maintenance_api.list(
        params={"tab": "mine"},
    )
    body = assert_response(response)

    orders = body['data']
    assert isinstance(orders, list)

    order_ids = [order["id"] for order in orders]
    assert order_id not in order_ids,"B 的“本人列表”不能包含 A 的工单"
    for item in orders:
        assert item["handlerId"] == created_second_worker["id"], (
            "本人列表只能返回当前维修工接取的工单"
        )


@pytest.mark.p0
@allure.title("维修工不能抢取其他维修工已接的工单")
def test_worker_cannot_grab_other_worker_order(
        created_maintenance,
        worker_maintenance_api,
        second_worker_maintenance_api,
        created_worker,
        created_second_worker,
):
    order_id = created_maintenance["id"]
    assert created_worker["id"] != created_second_worker["id"]

    # A 先抢单。
    response = worker_maintenance_api.grab(order_id)
    body = assert_true_response(response)

    # B 再抢同一张工单。
    response = second_worker_maintenance_api.grab(order_id)
    body = assert_response(response, code=500)
    assert body["message"] == "仅待处理工单可抢单"

    # B 抢单失败后，通过 A 查询工单归属。
    response = worker_maintenance_api.detail(order_id)
    body = assert_response(response)

    order = body["data"]
    assert_order_identity(order, created_maintenance, status=1)
    assert_worker_assignment(order, created_worker['id'])


@pytest.mark.p0
@allure.title("两个维修工同时抢单只能一人成功")
@pytest.mark.parametrize("round_no", range(1, 11))
def test_only_one_worker_can_grab_order(
        round_no,
        created_maintenance,
        worker_maintenance_api,
        second_worker_maintenance_api,
        created_worker,
        created_second_worker,
        tenant_maintenance_api,
):
    order_id = created_maintenance["id"]
    assert created_worker["id"] != created_second_worker["id"]

    barrier = Barrier(2)

    def grab_together(api):
        # 两个线程都准备好后，再分别发送抢单请求。
        barrier.wait(timeout=10)
        return api.grab(order_id)

    workers = [
        (created_worker["id"], worker_maintenance_api),
        (created_second_worker["id"], second_worker_maintenance_api),
    ]

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            (worker_id, pool.submit(grab_together, api))
            for worker_id, api in workers
        ]
        results = [
            (worker_id, future.result(timeout=20))
            for worker_id, future in futures
        ]
    success_ids = []
    failed_bodies = []

    for worker_id, response in results:
        assert response.status_code == 200

        body = response.json()

        if body["code"] == 200:
            assert body["data"] is True
            success_ids.append(worker_id)
        else:
            assert body["code"] == 500
            assert body["message"] in (
                "仅待处理工单可抢单",
                "抢单失败，工单可能已被抢走",
            )
            failed_bodies.append(body)

    assert len(success_ids) == 1, (
        f"第 {round_no} 轮：应恰好一人抢单成功"
    )
    assert len(failed_bodies) == 1, (
        f"第 {round_no} 轮：应恰好一人抢单失败"
    )

    # 前面已确认只有一人成功，取出赢家的账号 ID。
    winner_id = success_ids[0]

    # 通过申请租客查询最终工单，A 或 B 获胜都能查询。
    response = tenant_maintenance_api.detail(order_id)
    body = assert_response(response)

    order = body["data"]
    assert_order_identity(order, created_maintenance, status=1)
    assert_worker_assignment(order, winner_id)
