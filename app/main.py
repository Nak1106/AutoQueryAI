import sys
import os
import datetime

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
from agents.router_agent import RouterAgent
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
    st.session_state.chat_history = []  # List of dicts: {role, type, content, timestamp}
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
        router = RouterAgent()
        user_input = st.chat_input("Ask a question about your data...")
        if user_input:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Add user message
            st.session_state.chat_history.append({
                'role': 'user', 'type': 'query', 'content': user_input, 'timestamp': now
            })
            llm = get_llm(model_type, model_key)
            sql_agent = SQLAgent(llm, model_type)
            explainer_agent = ExplainerAgent(llm, model_type)
            chart_agent = ChartAgent(llm, model_type)
            intent = router.route(user_input)
            with st.spinner("Thinking..."):
                try:
                    if intent == 'sql':
                        sql_query = sql_agent.nl_to_sql(user_input, st.session_state.schema, st.session_state.chat_history)
                        result_df = execute_sql(st.session_state.df, sql_query)
                        explanation = explainer_agent.explain(sql_query, result_df.head())
                        msg = {
                            'role': 'assistant',
                            'type': 'query',
                            'sql': sql_query,
                            'result': result_df.head(),
                            'explanation': explanation,
                            'timestamp': now
                        }
                        # Chart if needed
                        if chart_agent.wants_chart(user_input):
                            chart_code = chart_agent.prompt_to_chart_code(user_input, st.session_state.schema, result_df)
                            try:
                                local_vars = {'result_df': result_df.copy()}
                                exec(chart_code, {}, local_vars)
                                fig = local_vars.get('fig', None)
                                if fig is not None:
                                    msg['chart'] = fig
                            except Exception as e:
                                msg['chart_error'] = str(e)
                        st.session_state.chat_history.append(msg)
                        st.toast("Query complete!", icon="✅")
                    elif intent == 'chart':
                        chart_code = chart_agent.prompt_to_chart_code(user_input, st.session_state.schema, st.session_state.df)
                        try:
                            local_vars = {'result_df': st.session_state.df.copy()}
                            exec(chart_code, {}, local_vars)
                            fig = local_vars.get('fig', None)
                            st.session_state.chat_history.append({
                                'role': 'assistant', 'type': 'plot', 'chart': fig, 'timestamp': now
                            })
                        except Exception as e:
                            st.session_state.chat_history.append({
                                'role': 'assistant', 'type': 'plot', 'chart_error': str(e), 'timestamp': now
                            })
                    elif intent == 'profiler':
                        profile = generate_profile(st.session_state.df)
                        st.session_state.chat_history.append({
                            'role': 'assistant', 'type': 'profile', 'profile': profile, 'timestamp': now
                        })
                    elif intent == 'explainer':
                        sql_query = ""
                        for msg in reversed(st.session_state.chat_history):
                            if msg['role'] == 'assistant' and msg.get('sql'):
                                sql_query = msg['sql']
                                break
                        explanation = explainer_agent.explain(sql_query, st.session_state.df.head())
                        st.session_state.chat_history.append({
                            'role': 'assistant', 'type': 'explanation', 'explanation': explanation, 'timestamp': now
                        })
                    else:
                        st.session_state.chat_history.append({
                            'role': 'assistant', 'type': 'error', 'content': str(intent), 'timestamp': now
                        })
                except Exception as e:
                    st.session_state.chat_history.append({
                        'role': 'assistant', 'type': 'error', 'content': f"Error: {e}", 'timestamp': now
                    })
                    st.toast(f"Query failed: {e}", icon="❌")
        # Render chat history stack
        for i, msg in enumerate(st.session_state.chat_history):
            if msg['role'] == 'user':
                with st.chat_message('user'):
                    st.markdown(f"**{i+1}.** {msg['content']}  \n*{msg['timestamp']}*")
            elif msg['role'] == 'assistant':
                with st.chat_message('assistant'):
                    st.subheader(f"Response {i+1}")
                    if msg['type'] == 'query':
                        st.markdown("**SQL Query:**")
                        st.code(msg['sql'], language='sql')
                        st.markdown("**Result:**")
                        st.dataframe(msg['result'])
                        st.markdown("**Explanation:**")
                        st.markdown(msg['explanation'])
                        st.toast("Explanation generated!", icon="💡")
                        if msg.get('chart'):
                            st.markdown("**Chart:**")
                            st.plotly_chart(msg['chart'], use_container_width=True)
                        if msg.get('chart_error'):
                            st.warning(f"Chart error: {msg['chart_error']}")
                    elif msg['type'] == 'plot':
                        st.markdown(f"Chart")
                        if msg.get('chart'):
                            st.plotly_chart(msg['chart'], use_container_width=True)
                        if msg.get('chart_error'):
                            st.warning(f"Chart error: {msg['chart_error']}")
                    elif msg['type'] == 'profile':
                        st.markdown(f"Data Profile")
                        st.json(msg['profile'])
                    elif msg['type'] == 'explanation':
                        st.markdown(f"Explanation")
                        st.markdown(msg['explanation'])
                        st.toast("Explanation generated!", icon="💡")
                    elif msg['type'] == 'error':
                        st.markdown(f"Error")
                        st.warning(msg['content'])
    else:
        st.info("Upload a file to start chatting.")

# --- Chat History Expander in Sidebar ---
with st.sidebar.expander("Chat History", expanded=False):
    for i, msg in enumerate(st.session_state.chat_history):
        if msg['role'] == 'user':
            st.markdown(f"**{i+1}. User:** {msg['content']}  \n*{msg['timestamp']}*")
        elif msg['role'] == 'assistant':
            if msg['type'] == 'query':
                st.markdown(f"**{i+1}. Assistant (Query):** SQL: `{msg['sql']}`  \n*{msg['timestamp']}*")
            elif msg['type'] == 'plot':
                st.markdown(f"**{i+1}. Assistant (Chart):** Chart  \n*{msg['timestamp']}*")
            elif msg['type'] == 'profile':
                st.markdown(f"**{i+1}. Assistant (Profile):** Data Profile  \n*{msg['timestamp']}*")
            elif msg['type'] == 'explanation':
                st.markdown(f"**{i+1}. Assistant (Explanation):** {msg['explanation']}  \n*{msg['timestamp']}*")
            elif msg['type'] == 'error':
                st.markdown(f"**{i+1}. Assistant (Error):** {msg['content']}  \n*{msg['timestamp']}*")
# --- Debug Tab ---
with tabs[3]:
    st.subheader("Debug / Logs")
    for log in st.session_state.logs:
        st.text(log)
