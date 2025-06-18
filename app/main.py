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
    st.session_state.chat_history = []  # List of dicts: {role, type, content, timestamp, message_id}
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'message_id_counter' not in st.session_state:
    st.session_state.message_id_counter = 0

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
            st.session_state.message_id_counter += 1
            msg_id = st.session_state.message_id_counter
            # Add user message
            st.session_state.chat_history.append({
                'role': 'user', 'type': 'query', 'content': user_input, 'timestamp': now, 'message_id': msg_id
            })
            llm = get_llm(model_type, model_key)
            sql_agent = SQLAgent(llm, model_type)
            explainer_agent = ExplainerAgent(llm, model_type)
            chart_agent = ChartAgent(llm, model_type)
            intent = router.route(user_input)
            st.toast(f"Routed to {intent.capitalize()} Agent", icon="🧠")
            with st.spinner("Thinking..."):
                try:
                    assistant_msg = {
                        'role': 'assistant',
                        'type': 'query',
                        'timestamp': now,
                        'message_id': msg_id
                    }
                    if intent == 'sql':
                        sql_query = sql_agent.nl_to_sql(user_input, st.session_state.schema, st.session_state.chat_history)
                        if not sql_query or sql_query.strip().lower() in ["none", "null", "", "-- error:"]:
                            st.toast("No SQL could be generated for this question.", icon="❌")
                        else:
                            result_df = execute_sql(st.session_state.df, sql_query)
                            try:
                                if result_df is None or not hasattr(result_df, 'empty') or result_df.empty:
                                    assistant_msg['explanation'] = "**Explanation:** No data returned."
                                    st.toast("No result returned for the SQL query.", icon="❌")
                                else:
                                    assistant_msg['sql'] = sql_query
                                    assistant_msg['result'] = result_df.head() if hasattr(result_df, 'head') else result_df
                                    assistant_msg['explanation'] = explainer_agent.explain(sql_query, result_df)
                                    st.toast("Explanation generated ✅", icon="🧠")
                                    if chart_agent.wants_chart(user_input):
                                        chart_code = chart_agent.prompt_to_chart_code(user_input, st.session_state.schema, result_df)
                                        try:
                                            local_vars = {'result_df': result_df.copy() if hasattr(result_df, 'copy') else result_df}
                                            exec(chart_code, {}, local_vars)
                                            fig = local_vars.get('fig', None)
                                            if fig is not None:
                                                assistant_msg['chart'] = fig
                                        except Exception as e:
                                            assistant_msg['chart_error'] = str(e)
                                    st.toast("Query complete!", icon="✅")
                            except Exception as e:
                                assistant_msg['content'] = f"Exception during result handling: {e}"
                    elif intent == 'chart':
                        chart_code = chart_agent.prompt_to_chart_code(user_input, st.session_state.schema, st.session_state.df)
                        try:
                            local_vars = {'result_df': st.session_state.df.copy() if hasattr(st.session_state.df, 'copy') else st.session_state.df}
                            exec(chart_code, {}, local_vars)
                            fig = local_vars.get('fig', None)
                            assistant_msg['type'] = 'plot'
                            assistant_msg['chart'] = fig
                        except Exception as e:
                            assistant_msg['type'] = 'plot'
                            assistant_msg['chart_error'] = str(e)
                    elif intent == 'profiler':
                        profile = generate_profile(st.session_state.df)
                        assistant_msg['type'] = 'profile'
                        assistant_msg['profile'] = profile
                    elif intent == 'explainer':
                        # Only run explainer if last assistant message has valid sql and result
                        last_sql = None
                        last_result = None
                        for msg in reversed(st.session_state.chat_history):
                            if msg['role'] == 'assistant' and msg.get('sql') and msg.get('result') is not None:
                                last_sql = msg['sql']
                                last_result = msg['result']
                                break
                        try:
                            if not last_sql or last_result is None or not hasattr(last_result, 'empty') or last_result.empty:
                                st.session_state["logs"].append("[main.py] Skipped explainer: No recent SQL + result.")
                            else:
                                assistant_msg['type'] = 'explanation'
                                assistant_msg['explanation'] = explainer_agent.explain(last_sql, last_result)
                                st.toast("Explanation generated ✅", icon="🧠")
                        except Exception as e:
                            assistant_msg['content'] = f"Exception during explainer handling: {e}"
                    else:
                        assistant_msg['type'] = 'error'
                        assistant_msg['content'] = f"Error: {intent}"
                    # Always ensure 'content' exists for error/fallback
                    if 'content' not in assistant_msg and not (
                        assistant_msg.get('sql') or
                        assistant_msg.get('explanation') or
                        assistant_msg.get('chart') or
                        assistant_msg.get('chart_error') or
                        assistant_msg.get('profile')
                    ):
                        assistant_msg['content'] = "No output generated."
                    # Only append if there is content
                    if not (
                        assistant_msg.get('sql') or
                        assistant_msg.get('explanation') or
                        assistant_msg.get('chart') or
                        assistant_msg.get('chart_error') or
                        assistant_msg.get('profile') or
                        assistant_msg.get('content')
                    ):
                        st.session_state["logs"].append("[main.py] Discarded assistant message: No content.")
                    else:
                        st.session_state.chat_history.append(assistant_msg)
                except Exception as e:
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'type': 'error',
                        'timestamp': now,
                        'message_id': msg_id,
                        'content': f"Error: {e}"
                    })
                    st.toast(f"Query failed: {e}", icon="❌")
        # Render chat history stack, grouping by message_id (user+assistant)
        grouped_msgs = []
        i = 0
        while i < len(st.session_state.chat_history):
            msg = st.session_state.chat_history[i]
            if msg['role'] == 'user':
                # Find the next assistant with same message_id
                user_msg = msg
                assistant_msg = None
                for j in range(i+1, len(st.session_state.chat_history)):
                    if st.session_state.chat_history[j]['role'] == 'assistant' and st.session_state.chat_history[j]['message_id'] == msg['message_id']:
                        assistant_msg = st.session_state.chat_history[j]
                        break
                grouped_msgs.append((user_msg, assistant_msg))
                i = j+1 if assistant_msg else i+1
            else:
                i += 1
        for idx, (user_msg, assistant_msg) in enumerate(grouped_msgs):
            with st.chat_message('user'):
                st.markdown(f"**{idx+1}.** {user_msg['content']}  \n*{user_msg['timestamp']}*")
            if assistant_msg:
                # Only render if there is actual content
                has_content = (
                    assistant_msg.get('sql') or assistant_msg.get('explanation') or assistant_msg.get('chart') or assistant_msg.get('chart_error') or assistant_msg.get('profile') or assistant_msg.get('content')
                )
                if not has_content:
                    continue
                with st.chat_message('assistant'):
                    st.subheader(f"Response {idx+1}")
                    t = assistant_msg.get('type')
                    if t == 'query':
                        if assistant_msg.get('sql'):
                            st.markdown("**SQL Query:**")
                            st.code(assistant_msg['sql'], language='sql')
                        if assistant_msg.get('result') is not None:
                            st.markdown("**Result:**")
                            st.dataframe(assistant_msg['result'])
                        if assistant_msg.get('explanation'):
                            st.markdown("**Explanation:**")
                            st.markdown(assistant_msg['explanation'])
                            st.toast("Explanation generated ✅", icon="🧠")
                        if assistant_msg.get('chart'):
                            st.markdown("**Chart:**")
                            st.plotly_chart(assistant_msg['chart'], use_container_width=True)
                        if assistant_msg.get('chart_error'):
                            st.warning(f"Chart error: {assistant_msg['chart_error']}")
                    elif t == 'plot':
                        st.markdown(f"Chart")
                        if assistant_msg.get('chart'):
                            st.plotly_chart(assistant_msg['chart'], use_container_width=True)
                        if assistant_msg.get('chart_error'):
                            st.warning(f"Chart error: {assistant_msg['chart_error']}")
                    elif t == 'profile':
                        st.markdown(f"Data Profile")
                        st.json(assistant_msg['profile'])
                    elif t == 'explanation':
                        # Fallback: if no recent valid SQL, show a friendly message
                        if not assistant_msg.get('explanation') or 'no recent query' in assistant_msg.get('explanation','').lower():
                            st.markdown("**Explanation:** No recent query found. Try asking something like 'What is the average fare?' or 'Show the highest tip.'")
                        else:
                            st.markdown(f"Explanation")
                            st.markdown(assistant_msg['explanation'])
                            st.toast("Explanation generated ✅", icon="🧠")
                    elif t == 'error':
                        st.markdown(f"Error")
                        st.warning(assistant_msg.get('content', 'Unknown error occurred.'))
# --- Route Log Expander ---
with st.expander("Routing & Classification Log", expanded=False):
    for log in st.session_state.logs:
        st.markdown(log)
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
