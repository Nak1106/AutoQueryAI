"""
Schema Embedder: Chunks, embeds, and retrieves relevant schema context for RAG.
"""
import faiss
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

class SchemaEmbedder:
    def __init__(self, embedding_model=None):
        self.embedding_model = embedding_model or OpenAIEmbeddings()
        self.vectorstore = None
        self.chunks = []

    def chunk_schema(self, schema_dict, chunk_size=5):
        # schema_dict: {table: [col1, col2, ...]}
        chunks = []
        for table, columns in schema_dict.items():
            for i in range(0, len(columns), chunk_size):
                chunk = f"Table: {table}\nColumns: {', '.join(columns[i:i+chunk_size])}"
                chunks.append(chunk)
        self.chunks = chunks
        return chunks

    def embed_chunks(self):
        if not self.chunks:
            raise ValueError("No schema chunks to embed.")
        self.vectorstore = FAISS.from_texts(self.chunks, self.embedding_model)

    def retrieve(self, query, k=3):
        if not self.vectorstore:
            raise ValueError("Vectorstore not initialized.")
        docs = self.vectorstore.similarity_search(query, k=k)
        return [doc.page_content for doc in docs]
