import os
import hashlib
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from app.core.logger import get_logger

logger = get_logger("INGESTION_SERVICE")


class IngestionService:
    def __init__(self):
        # API en la nube: 0 bytes de descarga de modelos
        self.embeddings = HuggingFaceEndpointEmbeddings(
            model="sentence-transformers/all-MiniLM-L6-v2",
            huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN")
        )
        self.db_path = "data/vector_db"

    def _calculate_hash(self, file_path):
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            hasher.update(f.read())
        return hasher.hexdigest()

    async def process_pdf(self, file_path: str):
        file_hash = self._calculate_hash(file_path)
        logger.info(f"Procesando PDF (Hash: {file_hash[:10]})")

        loader = PyPDFLoader(file_path)
        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = splitter.split_documents(docs)

        # Guardamos en FAISS (ligero y rápido)
        vector_db = FAISS.from_documents(chunks, self.embeddings)
        vector_db.save_local(self.db_path)

        return len(chunks)