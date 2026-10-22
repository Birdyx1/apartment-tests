from pathlib import Path
import yaml

def load_login_cases():
    path = Path(__file__).parent /"data"/ "login_cases.yaml"
    with path.open(encoding="utf-8") as file:
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
        missing = required - case.keys()
        if missing:
            raise ValueError(f"第{index}条数据缺少{missing}")
        case_id = case["case_id"]
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"第{index}条数据的case_id必须是非空字符串")
        if not isinstance(case['password'], str):
            raise ValueError(f"第{index}条数据的password必须是字符串")
        for field in ("expected_http", "expected_code"):
            if type(case[field]) is not int:
                raise ValueError(f"第{index}条数据的{field}必须是整数")
        message = case["expected_message"]
        if not isinstance(message, str) or not message.strip():
            raise ValueError(f"第{index}条数据的expected_message必须是非空字符串")
        if case_id in seen_id:
            raise ValueError(f"case_id {case_id} 重复")
        seen_id.add(case_id)
    return cases


