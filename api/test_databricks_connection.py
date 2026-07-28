from dotenv import load_dotenv
import os
from databricks import sql

load_dotenv()

server_hostname = os.getenv("DATABRICKS_SERVER_HOSTNAME")
http_path = os.getenv("DATABRICKS_HTTP_PATH")
access_token = os.getenv("DATABRICKS_TOKEN")

connection = sql.connect(
    server_hostname=server_hostname,
    http_path=http_path,
    access_token=access_token
)

cursor = connection.cursor()
cursor.execute("SELECT * FROM aegis.gold.monthly_revenue LIMIT 5")
result = cursor.fetchall()

for row in result:
    print(row)

cursor.close()
connection.close()


#----------------------------------------------
from databricks.sdk import WorkspaceClient
import os
from dotenv import load_dotenv

load_dotenv()

w = WorkspaceClient(
    host=os.getenv("server_hostname"),  # same env var as before, but SDK might want it named differently — check the doc
    token=os.getenv("access_token")
)

job_id = 941139808755098  # your actual job ID, as an integer

runs = w.jobs.list_runs(job_id=job_id)
for run in runs:
    print(run.run_id, run.state.result_state, run.state.state_message)