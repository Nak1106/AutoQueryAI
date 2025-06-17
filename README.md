# AutoQueryAI

**AutoQueryAI** is an advanced LLM-powered data analytics assistant that enables users to upload structured data, ask natural language questions, and receive SQL/pandas code, explanations, and visualizations. It supports multi-turn chat, RAG for schema retrieval, and model switching (Groq, HuggingFace, OpenAI).

## Features
- Upload CSV, Excel, JSON, or SQL dump files
- Natural language to SQL/pandas code generation (LLM-powered)
- Code execution and result display
- Natural language explanations of results
- Automatic data visualization (bar, line, pie)
- ER diagram and data profiling summaries
- Multi-turn chat with memory
- RAG for schema chunking
- Switch between Groq, HuggingFace, OpenAI models
- Deployable via Docker or Streamlit Cloud

## Project Structure
```
app/      # Streamlit interface
core/     # Data parsing, schema, query execution
agents/   # Prompt logic (SQL, explainer, chart, profiler, embed)
models/   # Chat history, memory, embedding store
utils/    # Helpers, ERD, profiling
config/   # .env templates, model keys
legacy/   # Reference implementation (app1.py)
docs/     # Diagrams, architecture, RAG flow
tests/    # Pytest-based tests
```

## Technologies Used
- Python, Streamlit, LangChain
- Groq (Mixtral), HuggingFace, OpenAI LLMs
- DuckDB/sqlite, pandas, ERAlchemy, pandas-profiling, Graphviz
- FAISS, HuggingFace embeddings
- Docker, Pytest

## Quick Start
1. Clone the repo
2. Run `setup.sh` or use Docker
3. Open Streamlit app and upload your data

## Architecture
See `docs/` for flow diagrams and architecture.

## Credits
- Reference implementation: `legacy/app1.py`

---

*For more details, see the documentation in the `docs/` folder.*
