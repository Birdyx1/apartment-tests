"""读取并检查登录 YAML 数据，为 Pytest 参数化提供列表中的每条用例。
加载失败会阻止收集该测试模块，避免错误数据被静默忽略。
"""

from pathlib import Path
import yaml

def load_login_cases():
    """读取 YAML 后逐项校验结构、必填字段、类型与唯一编号；不发送接口请求。"""
    # 以当前文件位置为基准，而非终端当前目录，避免换目录后找不到 YAML。
    path = Path(__file__).parent /"data"/ "login_cases.yaml"
    with path.open(encoding="utf-8") as file:
        # safe_load 将 YAML 列表/映射转为 Python list/dict，不执行 YAML 中的对象构造。
        cases = yaml.safe_load(file)

    if not isinstance(cases, list) or not cases:
        raise ValueError("登录数据必须是非空列表")

    required = {
        "case_id",
        "password",
        "expected_http",
        "expected_code",
        "expected_message",
    }
    seen_id = set()
    # 这些检查用于防止空文件、字段遗漏或重复编号造成漏测。
    for index,case in enumerate(cases,start=1):
        if not isinstance(case, dict):
            raise ValueError(f"第{index}条数据必须是字典")
        # 集合相减得到缺失字段；先检查存在，再用 case[字段] 读取。
        missing = required - case.keys()
        if missing:
            raise ValueError(f"第{index}条数据缺少{missing}")
        case_id = case["case_id"]
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"第{index}条数据的case_id必须是非空字符串")
        if not isinstance(case['password'], str):
            raise ValueError(f"第{index}条数据的password必须是字符串")
        for field in ("expected_http", "expected_code"):
            # Python 的 bool 是 int 的子类，严格类型检查才能拒绝 true/false。
            if type(case[field]) is not int:
                raise ValueError(f"第{index}条数据的{field}必须是整数")
        message = case["expected_message"]
        if not isinstance(message, str) or not message.strip():
            raise ValueError(f"第{index}条数据的expected_message必须是非空字符串")
        # 每出现一个新编号就记录，下一条重复时明确报错，防止报告名称混淆。
        if case_id in seen_id:
            raise ValueError(f"case_id {case_id} 重复")
        seen_id.add(case_id)
    return cases


