import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch
from app.service.ingestion_service import IngestionService

@pytest.mark.asyncio
async def test_calculate_hash(tmp_path):
    d = tmp_path / "test.txt"
    d.write_text("hello world")
    
    service = IngestionService()
    h = service._calculate_hash(str(d))
    assert len(h) == 64 # SHA256 length

@pytest.mark.asyncio
async def test_process_pdf_failure():
    service = IngestionService()
    # Test with non-existent file
    with pytest.raises(Exception):
        await service.process_pdf("non_existent.pdf")

@pytest.mark.asyncio
async def test_process_pdf_success(tmp_path):
    pdf = tmp_path / "test.pdf"
    pdf.write_text("%PDF-1.4 test")
    
    service = IngestionService()
    
    with patch("app.service.ingestion_service.PyPDFLoader") as mock_loader:
        # Simulate loading documents
        mock_loader.return_value.load.return_value = [MagicMock(page_content="text")]
        # Mock RecursiveCharacterTextSplitter
        with patch("app.service.ingestion_service.RecursiveCharacterTextSplitter") as mock_splitter:
            mock_splitter.return_value.split_documents.return_value = [MagicMock(page_content="chunk1")]
            # Mock FAISS
            with patch("app.service.ingestion_service.FAISS") as mock_faiss:
                mock_faiss.from_documents.return_value = MagicMock()
                
                chunks = await service.process_pdf(str(pdf))
                assert chunks == 1
                mock_faiss.from_documents.assert_called_once()

@pytest.mark.asyncio
async def test_search_in_vector_db_success():
    service = IngestionService()
    with patch("os.path.exists", return_value=True):
        with patch("app.service.ingestion_service.FAISS.load_local") as mock_load:
            mock_db = MagicMock()
            mock_db.similarity_search.return_value = [MagicMock(page_content="found text")]
            mock_load.return_value = mock_db
            
            result = await service.search_in_vector_db("query")
            assert "found text" in result

@pytest.mark.asyncio
async def test_search_in_vector_db_failure():
    service = IngestionService()
    with patch("os.path.exists", return_value=True):
        with patch("app.service.ingestion_service.FAISS.load_local", side_effect=Exception("Load fail")):
            from app.core.exceptions import IngestionError
            with pytest.raises(IngestionError):
                await service.search_in_vector_db("query")

@pytest.mark.asyncio
async def test_search_no_db():
    service = IngestionService()
    with patch("os.path.exists", return_value=False):
        with pytest.raises(Exception) as exc:
            await service.search_in_vector_db("query")
        assert "No documents uploaded" in str(exc.value)
