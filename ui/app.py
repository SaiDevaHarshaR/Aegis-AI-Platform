import streamlit as st
import requests

st.title("Aegis AI Platform")
API_URL = "http://localhost:8000"

try:
    resp = requests.get(f"{API_URL}/health")
    if resp.status_code == 200:
        st.success("API Online")
    else:
        st.error("API Offline")
except requests.exceptions.RequestException:
    st.error("API Offline")

st.header("Knowledge Base (RAG)")
question = st.text_input("Ask a question about Aegis:")

if st.button("Ask"):
    answer = requests.post(url='http://localhost:8000/rag/ask', json={"question" : question})
    response = answer.json()
    st.write(response)

#---------------------------------------------------------

st.header("Analytics")
question_a = st.text_input("Ask a question about analytics:")

if st.button("Ask1"):
    answer1 = requests.post(url='http://localhost:8000/analytics/ask', json={"question" : question_a})
    response1 = answer1.json()
    st.write(response1)

#---------------------------------------------------------

st.header("Monitoring")
error_message = st.text_input("What error message did you get? ")
job_name = st.text_input("What is the name of the job?")

if st.button("Ask2"):
    answer2 = requests.post(url='http://localhost:8000/monitoring/diagnose', json={"error_message" : error_message, "job_name" : job_name})
    response2 = answer2.json()
    st.write(response2)

#---------------------------------------------------------

st.header("Ingestion")
file_path = st.text_input("Give path of the file: ")
table_name = st.text_input("Give name of the table: ")

if st.button("Ask3"):
    answer3 = requests.post(url='http://localhost:8000/ingestion/assess', json={"file_path" : file_path, "table_name" : table_name})
    response3 = answer3.json()
    st.write(response3)