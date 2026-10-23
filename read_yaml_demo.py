"""YAML 读取学习演示；手动执行会打印数据，不参与 Pytest 测试收集。
正式用例使用 data_loader.py，勿在演示数据中放真实密码或令牌。
"""

from pathlib import Path

import yaml

path = Path(__file__).parent / "data" / "login_cases.yaml"

with path.open(encoding="utf-8") as file:
    cases = yaml.safe_load(file)

print(type(cases))
print(cases)
print(cases[0]["expected_code"])
