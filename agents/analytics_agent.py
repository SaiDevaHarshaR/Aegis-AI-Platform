from pydantic import BaseModel
import ollama
from databricks import sql as databricks_sql
from dotenv import load_dotenv
import os

class SQLGeneration(BaseModel):
    sql_query: str
    explanation: str

def is_safe_select_query(query: str) -> bool:
    query_clean = query.strip().lower()
    starts_with_select = query_clean.startswith("select")
    no_multiple_statements = ";" not in query_clean.rstrip(";")
    return starts_with_select and no_multiple_statements

def build_sql_prompt(question: str) -> str:
    prompt = f"""
You are a SQL assistant. Generate a SQL query to answer the question, using ONLY this table:

Table: aegis.gold.monthly_revenue
Columns: year (int), month (int), total_revenue (double)

Rules:
- Only generate SELECT queries. Never generate INSERT, UPDATE, DELETE, DROP, or TRUNCATE.
- Use standard SQL syntax compatible with Databricks SQL.

Question: {question}
You MUST use the full three-part table name aegis.gold.monthly_revenue in your FROM clause. Never use just monthly_revenue

Respond with the SQL query and a brief explanation of what it does.
"""
    return prompt

load_dotenv()

def ask_analytics_agent(question: str):
    prompt = build_sql_prompt(question)
    resp = ollama.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': prompt}],
        format=SQLGeneration.model_json_schema()
    )
    generation = SQLGeneration.model_validate_json(resp['message']['content'])
    corrected_query = generation.sql_query.replace("FROM monthly_revenue", "FROM aegis.gold.monthly_revenue")
    corrected_query = corrected_query.replace("from monthly_revenue", "FROM aegis.gold.monthly_revenue")
    if not is_safe_select_query(corrected_query):
        return {"error": "Unsafe query blocked", "attempted_query": corrected_query}

    connection = databricks_sql.connect(
        server_hostname=os.getenv("DATABRICKS_SERVER_HOSTNAME"),
        http_path=os.getenv("DATABRICKS_HTTP_PATH"),
        access_token=os.getenv("DATABRICKS_TOKEN")
    )
    cursor = connection.cursor()
    print("Generated SQL:", corrected_query)
    cursor.execute(corrected_query)
    result = cursor.fetchall()
    cursor.close()
    connection.close()

    return {
    "sql_query": corrected_query,
    "explanation": generation.explanation,
    "result": result
}

if __name__ == "__main__":
    result = ask_analytics_agent("What was our total revenue in 2017?")
    print(result)