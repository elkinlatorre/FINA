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

    def _get_user_db_path(self, user_id: str) -> str:
        """Returns the specific path for a user's vector database."""
        return os.path.join(settings.VECTOR_DB_PATH, user_id)

    async def process_pdf(self, file_path: str, user_id: str) -> int:
        """Process PDF file and store in user-specific vector database.
        
        Args:
            file_path: Path to the PDF file
            user_id: ID of the user owning the document
            
        Returns:
            Number of chunks processed
            
        Raises:
            IngestionError: If PDF processing fails or constraints are violated
        """
        # Validate file size
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > settings.MAX_PDF_SIZE_MB:
            raise IngestionError(f"File too large ({file_size_mb:.2f}MB). Max allowed: {settings.MAX_PDF_SIZE_MB}MB")

        try:
            file_hash = self._calculate_hash(file_path)
            logger.info(f"Processing PDF for user {user_id} (Hash: {file_hash[:10]})")

            loader = PyPDFLoader(file_path)
            docs = loader.load()

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP
            )
            chunks = splitter.split_documents(docs)

            # Save to user-specific FAISS index
            user_db_path = self._get_user_db_path(user_id)
            vector_db = FAISS.from_documents(chunks, self.embeddings)
            vector_db.save_local(user_db_path)

            return len(chunks)
        except Exception as e:
            logger.error(f"PDF processing failed for user {user_id}: {str(e)}")
            raise IngestionError(f"Failed to process PDF: {str(e)}")

    async def search_in_vector_db(self, query: str, user_id: str, k: int = 3) -> str:
        """Search for relevant document chunks in user-specific FAISS database.
        
        Args:
            query: Search query
            user_id: ID of the user whose docs to search
            k: Number of results to return
            
        Returns:
            Concatenated relevant document chunks
            
        Raises:
            IngestionError: If vector database doesn't exist or search fails
        """
        user_db_path = self._get_user_db_path(user_id)
        if not os.path.exists(user_db_path):
            logger.warning(f"Search failed: No documents found for user {user_id}")
            return "No documents found to answer this query. Please upload a relevant financial PDF first."

        try:
            # Load user-specific vector database
            vector_db = FAISS.load_local(
                user_db_path,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            
            # Search for similar documents
            docs = vector_db.similarity_search(query, k=k)
            
            # Concatenate and return results
            return "\n\n".join([d.page_content for d in docs])
        except Exception as e:
            logger.error(f"Vector search failed for user {user_id}: {str(e)}")
            raise IngestionError(f"Failed to search documents: {str(e)}")

    async def cleanup_user_data(self, user_id: str):
        """Deletes all vector data associated with a user."""
        user_db_path = self._get_user_db_path(user_id)
        if os.path.exists(user_db_path):
            import shutil
            logger.info(f"🗑️ Cleaning up ephemeral RAG data for user {user_id}")
            shutil.rmtree(user_db_path)
