from pathlib import Path

import yaml

path = Path(__file__).parent / "data" / "login_cases.yaml"

with path.open(encoding="utf-8") as file:
    cases = yaml.safe_load(file)

print(type(cases))
print(cases)
print(cases[0]["expected_code"])