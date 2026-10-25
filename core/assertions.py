"""公共响应校验：只合并重复的 HTTP/业务码检查，不替代业务断言。"""


def assert_response(response, *, http_status=200, code=200):
    """校验响应并返回 JSON；错误码也必须由调用处明确传入。"""
    __tracebackhide__ = True
    assert response.status_code == http_status, (
        f"预期 HTTP {http_status}，实际 {response.status_code}"
    )
    body = response.json()
    assert isinstance(body, dict), "接口应返回 JSON 对象"
    assert body["code"] == code, (
        f"预期业务码 {code}，实际 {body.get('code')}：{body.get('message')}"
    )
    return body


def assert_true_response(response):
    """校验返回 data=true 的成功操作，例如抢单、接单和模拟确认。"""
    body = assert_response(response)
    assert body["data"] is True, "操作成功时 data 应为 true"
    return body
