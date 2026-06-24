from workflow import run_workflow
import json

verified_skills = [
    "Python",
    "FastAPI"
]

result = run_workflow(verified_skills)

print(json.dumps(result, indent=4))