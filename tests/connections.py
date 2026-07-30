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
