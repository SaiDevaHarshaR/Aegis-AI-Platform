from databricks.sdk import WorkspaceClient
import os
from pydantic import BaseModel
import ollama
from dotenv import load_dotenv

load_dotenv()

w = WorkspaceClient(
    host=os.getenv("DATABRICKS_SERVER_HOSTNAME"),
    token=os.getenv("DATABRICKS_TOKEN")
)

job_id = 941139808755098



class RootCauseAnalysis(BaseModel):
    likely_root_cause: str
    suggested_fix: str
    confidence: float
    requires_human_review: bool

def build_rca_prompt(error_message: str, job_name: str) -> str:
    prompt = f"""
You are a data platform SRE assistant. A Databricks job named "{job_name}" failed with this error:

{error_message}

Analyze the error and provide:
- likely_root_cause: a plain-English explanation of what went wrong
- suggested_fix: a concrete, actionable fix
- confidence: how confident you are (0-1)
- requires_human_review: true if this needs a human to verify before acting, false if it's safe to trust
"""
    return prompt

def diagnose_failure(error_message: str, job_name: str) -> RootCauseAnalysis:
    prompt = build_rca_prompt(error_message, job_name)
    resp = ollama.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': prompt}],
        format=RootCauseAnalysis.model_json_schema()
    )
    return RootCauseAnalysis.model_validate_json(resp['message']['content'])
if __name__ == "__main__":
    runs = w.jobs.list_runs(job_id=job_id)
    for run in runs:
        print(run.run_id, run.state.result_state, run.state.state_message)
        run_details = w.jobs.get_run(run_id=256369913679791)
        task_run_id = run_details.tasks[0].run_id
        print("Task run ID:", task_run_id)
        output = w.jobs.get_run_output(run_id=task_run_id)
        print(output.error)

    result = diagnose_failure(output.error, "test_failing_job")
    print(result)
