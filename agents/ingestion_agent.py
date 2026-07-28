from pydantic import BaseModel
import pandas as pd
class ColumnAnomaly(BaseModel):
    column_name: str
    issue_type: str
    confidence: float
    explanation: str


class SchemaAssessment(BaseModel):
    anomalies: list[ColumnAnomaly]
    overall_confidence: float
    recommendation: str

def get_sample_rows(file_path: str, n: int = 10):
    df = pd.read_csv(file_path)
    return df.head(n)

KNOWN_SCHEMAS = {
    "customers": ["customer_id", "customer_unique_id", "customer_zip_code_prefix", "customer_city", "customer_state"],
    "products" : ["product_id","product_category_name","product_name_lenght","product_description_lenght","product_photos_qty","product_weight_g","product_length_cm","product_height_cm","product_width_cm"]
}
def get_existing_schema(table_name: str) -> list[str]:
    return KNOWN_SCHEMAS.get(table_name, [])

def build_prompt(new_file_columns: list[str], sample_rows, existing_schema: list[str]) -> str:
    prompt = f"""
You are comparing two lists of column names.

LIST A (columns in the NEW file): {new_file_columns}
LIST B (columns EXPECTED, from the existing table): {existing_schema}

Task: go through LIST A one column at a time. For each column in LIST A, check: does this EXACT name appear in LIST B?
- If yes, it is NOT an anomaly, skip it.
- If no, decide: is it likely a renamed version of a column in LIST B (similar meaning/position), or a genuinely new/unexpected column?

Only report anomalies for columns that are NOT found in LIST B.
Do not report a column as an anomaly if it appears in LIST B, even with different capitalization.

Sample data for context:
{sample_rows.to_string()}

Respond with anomalies found (empty list if none), overall_confidence, and recommendation.
"""
    return prompt

import ollama

def assess_schema(file_path: str, table_name: str) -> SchemaAssessment:
    sample_rows = get_sample_rows(file_path)
    new_file_columns = list(sample_rows.columns)
    existing_schema = get_existing_schema(table_name)

    prompt = build_prompt(new_file_columns, sample_rows, existing_schema)

    resp = ollama.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': prompt}],
        format=SchemaAssessment.model_json_schema()
    )

    return SchemaAssessment.model_validate_json(resp.message.content)
result = assess_schema("data/raw/olist_customers_test.csv", "customers")
print(result)