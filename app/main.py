import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Now your imports should work
from core.file_parser import parse_file
import streamlit as st
import pandas as pd
import os
from core.file_parser import parse_file
from core.schema_handler import preview_schema, generate_profile
from utils.erd import generate_erd
from utils.profiling import generate_profile_report
from agents.sql_agent import SQLAgent
from agents.explainer_agent import ExplainerAgent
from agents.chart_agent import ChartAgent
from core.query_executor import execute_sql, execute_pandas_code
from models.chat_history import ChatHistory
from config.model_config import MODELS, get_model_key
from dotenv import load_dotenv
from llm_loader import get_llm
import os
import io
import plotly.io as pio


# --- Load environment variables from .env or .env.template ---
root_dir = os.path.dirname(os.path.dirname(__file__))
env_path = os.path.join(root_dir, '.env')
template_path = os.path.join(root_dir, '.env.template')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv(template_path)

st.set_page_config(page_title="AutoQueryAI", layout="wide")
st.title("AutoQueryAI - LLM Data Analytics Assistant")

# --- Sidebar: Model selector, file upload, schema preview, LLM status ---
st.sidebar.header("Settings")
model_name = st.sidebar.selectbox("Select LLM Model", list(MODELS.keys()))
model_key = get_model_key(MODELS[model_name])

# --- LLM connection status check ---
def check_llm_status(model_type, api_key):
    try:
        from app.llm_loader import get_llm
        llm = get_llm(model_type, api_key)
        # Test call
        if model_type == 'mistral':
            resp = llm.invoke("SELECT * FROM customers LIMIT 5")
            return True, "Mistral model connected"
        elif model_type == 'hf':
            resp = llm("SELECT * FROM customers LIMIT 5", max_new_tokens=10)
            return True, "HF model connected"
    except Exception as e:
        return False, str(e)

model_type = MODELS[model_name]
status_ok, status_msg = check_llm_status(model_type, model_key)
if status_ok:
    st.sidebar.success(f"✅ {status_msg}")
else:
    st.sidebar.error(f"❌ {status_msg}")

uploaded_file = st.sidebar.file_uploader("Upload CSV, Excel, JSON, or SQL", type=["csv", "xlsx", "xls", "json", "sql"])

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = ChatHistory()
if 'df' not in st.session_state:
    st.session_state.df = None
if 'schema' not in st.session_state:
    st.session_state.schema = None
if 'logs' not in st.session_state:
    st.session_state.logs = []

# --- File parsing and schema extraction ---
if uploaded_file:
    file_path = os.path.join("/tmp", uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    try:
        df, schema = parse_file(file_path)
        st.session_state.df = df
        st.session_state.schema = schema
        st.session_state.logs.append(f"Loaded file: {uploaded_file.name}")
    except Exception as e:
        st.error(f"File parsing error: {e}")
        st.session_state.logs.append(f"Error: {e}")

# --- Tabs: Chat | Schema | ERD/Profile | Debug ---
tabs = st.tabs(["Chat", "Schema", "ERD/Profile", "Debug"])

# --- Schema Tab ---
with tabs[1]:
    if st.session_state.schema:
        st.subheader("Schema Preview")
        st.code(preview_schema(st.session_state.schema))
        st.write(f"Rows: {st.session_state.schema['num_rows']}")
        st.write(f"Columns: {st.session_state.schema['num_columns']}")
    else:
        st.info("Upload a file to see schema preview.")

# --- ERD/Profile Tab ---
with tabs[2]:
    if st.session_state.df is not None:
        st.subheader("Profiling Summary")
        profile = generate_profile(st.session_state.df)
        st.json(profile)
        # Optionally, generate ERD (if SQL)
        if uploaded_file and uploaded_file.name.endswith('.sql'):
            erd_path = os.path.join("/tmp", "erd.png")
            try:
                generate_erd(f"duckdb:///{file_path}", erd_path)
                st.image(erd_path, caption="ER Diagram")
            except Exception as e:
                st.warning(f"ERD generation failed: {e}")
    else:
        st.info("Upload a file to see profiling or ERD.")

# --- Chat Tab ---
with tabs[0]:
    st.subheader("Chat with your data")
    if st.session_state.df is not None:
        for msg in st.session_state.chat_history.get_history():
            with st.chat_message(msg['role']):
                st.markdown(msg['content'])
        user_input = st.chat_input("Ask a question about your data...")
        if user_input:
            st.session_state.chat_history.add_message('user', user_input)
            llm = get_llm(model_type, model_key)
            sql_agent = SQLAgent(llm, model_type)
            explainer_agent = ExplainerAgent(llm, model_type)
            chart_agent = ChartAgent(llm, model_type)
            with st.spinner("Generating SQL query..."):
                sql_query = sql_agent.nl_to_sql(user_input, st.session_state.schema, st.session_state.chat_history.get_history())
            st.session_state.logs.append(f"Generated SQL: {sql_query}")
            try:
                with st.spinner("Running query..."):
                    result_df = execute_sql(st.session_state.df, sql_query)
                st.session_state.chat_history.add_message('assistant', f"SQL Query:\n```sql\n{sql_query}\n```")
                st.session_state.chat_history.add_message('assistant', f"Result:\n{result_df.head().to_markdown(index=False)}")
                st.dataframe(result_df)
                # CSV export
                csv = result_df.to_csv(index=False).encode('utf-8')
                st.download_button("Download CSV", csv, "result.csv", "text/csv")
                # Explanation
                with st.spinner("Explaining result..."):
                    explanation = explainer_agent.explain(sql_query, result_df.head())
                st.markdown(f"**Explanation:**\n{explanation}")
                # Chart
                if chart_agent.wants_chart(user_input):
                    with st.spinner("Generating chart..."):
                        chart_code = chart_agent.prompt_to_chart_code(user_input, st.session_state.schema, result_df)
                    try:
                        local_vars = {'result_df': result_df.copy()}
                        exec(chart_code, {}, local_vars)
                        fig = local_vars.get('fig', None)
                        if fig is not None:
                            st.plotly_chart(fig, use_container_width=True)
                            # PNG export
                            buf = io.BytesIO()
                            pio.write_image(fig, buf, format='png')
                            st.download_button("Download Chart as PNG", buf.getvalue(), "chart.png", "image/png")
                    except Exception as e:
                        st.warning(f"Chart rendering failed: {e}")
                st.toast("Query complete!", icon="✅")
            except Exception as e:
                st.session_state.chat_history.add_message('assistant', f"Error executing query: {e}")
                st.error(f"Query error: {e}")
                st.toast(f"Query failed: {e}", icon="❌")
    else:
        st.info("Upload a file to start chatting.")

# --- Debug Tab ---
with tabs[3]:
    st.subheader("Debug / Logs")
    for log in st.session_state.logs:
        st.text(log)
