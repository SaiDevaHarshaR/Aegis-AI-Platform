from fastapi import FastAPI
from pydantic import BaseModel
from agents.rag_agent import build_index, answer_question, chunk_text
from agents.analytics_agent import ask_analytics_agent
from agents.monitoring_agent import diagnose_failure
from agents.ingestion_agent import assess_schema
app = FastAPI()

with open("docs/architecture.md", "r", encoding="utf-8") as f:
    text = f.read()
documents = chunk_text(text)
index = build_index(documents)

class QuestionRequest(BaseModel):
    question: str
class DaignoseRequest(BaseModel):
    error_message: str
    job_name: str 
class IngestionRequest(BaseModel):
    file_path: str
    table_name: str

@app.get("/")
def read_root():
    return {"message": "Aegis API is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/rag/ask")
async def ask(request: QuestionRequest):
    ans = answer_question(request.question, index, documents)
    return {"answer": ans}

@app.post("/analytics/ask")
async def analytics(request: QuestionRequest):
    an_ans = ask_analytics_agent(request.question)
    return {"answer": an_ans}

@app.post("/monitoring/diagnose")
async def monitoring(request: DaignoseRequest):
    wis = diagnose_failure(request.error_message, request.job_name)
    return {"answer": wis}

@app.post("/ingestion/assess")
async def ingestion(request: IngestionRequest):
    try:
        whyisthis = assess_schema(request.file_path, request.table_name)
        return {"answer": whyisthis}
    except FileNotFoundError:
        return {"error": f"File not found: {request.file_path}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}