import hashlib
import os

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.exceptions import IngestionError
from app.core.logger import get_logger
from app.core.settings import settings

logger = get_logger("INGESTION_SERVICE")


class IngestionService:
    def __init__(self):
        # Cloud API: 0 bytes of model downloads
        self.embeddings = HuggingFaceEndpointEmbeddings(
            model=settings.EMBEDDING_MODEL,
            huggingfacehub_api_token=settings.HUGGINGFACEHUB_API_TOKEN
        )
        self.db_path = settings.VECTOR_DB_PATH

    def _calculate_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file for deduplication."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            hasher.update(f.read())
        return hasher.hexdigest()

    async def process_pdf(self, file_path: str) -> int:
        """Process PDF file and store in vector database.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Number of chunks processed
            
        Raises:
            IngestionError: If PDF processing fails
        """
        try:
            file_hash = self._calculate_hash(file_path)
            logger.info(f"Processing PDF (Hash: {file_hash[:10]})")

            loader = PyPDFLoader(file_path)
            docs = loader.load()

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP
            )
            chunks = splitter.split_documents(docs)

            # Save to FAISS (lightweight and fast)
            vector_db = FAISS.from_documents(chunks, self.embeddings)
            vector_db.save_local(self.db_path)

            return len(chunks)
        except Exception as e:
            logger.error(f"PDF processing failed: {str(e)}")
            raise IngestionError(f"Failed to process PDF: {str(e)}")

    async def search_in_vector_db(self, query: str, k: int = 3) -> str:
        """Search for relevant document chunks in FAISS vector database.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            Concatenated relevant document chunks
            
        Raises:
            IngestionError: If vector database doesn't exist or search fails
        """
        if not os.path.exists(settings.VECTOR_DB_PATH):
            raise IngestionError("No documents uploaded to the system")

        try:
            # Load vector database
            vector_db = FAISS.load_local(
                settings.VECTOR_DB_PATH,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            
            # Search for similar documents
            docs = vector_db.similarity_search(query, k=k)
            
            # Concatenate and return results
            return "\n\n".join([d.page_content for d in docs])
        except Exception as e:
            logger.error(f"Vector search failed: {str(e)}")
            raise IngestionError(f"Failed to search documents: {str(e)}")