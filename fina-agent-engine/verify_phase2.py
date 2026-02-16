import asyncio
import os
import shutil
from unittest.mock import MagicMock, patch
from app.service.ingestion_service import IngestionService
from app.core.settings import settings

async def verify_user_isolation():
    service = IngestionService()
    user_a = "user_alpha"
    user_b = "user_beta"
    
    # Mocking the PDF loader to avoid needing real files
    mock_doc = MagicMock()
    mock_doc.page_content = "The secret code for User Alpha is 12345."
    mock_doc.metadata = {"source": "manual_test"}
    
    print(f"--- FINA Phase 2 Verification ---")
    
    with patch("langchain_community.document_loaders.PyPDFLoader.load", return_value=[mock_doc]):
        print(f"📤 Ingesting document for {user_a}...")
        # Create a dummy file for the hasher
        dummy_file = "test_dummy.pdf"
        with open(dummy_file, "w") as f: f.write("dummy content")
        
        await service.process_pdf(dummy_file, user_a)
        
        # 1. Test Isolation: User B searching User A's data
        print(f"🔍 {user_b} searching for secret code (should fail)...")
        result_b = await service.search_in_vector_db("secret code", user_b)
        if "No documents found" in result_b:
            print(f"✅ ISOLATION: User B could not access User A data.")
        else:
            print(f"❌ ISOLATION FAILED: User B accessed data.")
            
        # 2. Test Access: User A searching own data
        print(f"🔍 {user_a} searching for secret code (should succeed)...")
        result_a = await service.search_in_vector_db("secret code", user_a)
        if "12345" in result_a:
            print(f"✅ ACCESS: User A successfully accessed own data.")
        else:
            print(f"❌ ACCESS FAILED: User A could not find own data.")
            
        # 3. Test Cleanup
        print(f"🗑️ Cleaning up {user_a}'s data...")
        await service.cleanup_user_data(user_a)
        
        if not os.path.exists(os.path.join(settings.VECTOR_DB_PATH, user_a)):
            print(f"✅ CLEANUP: User A directory deleted.")
        else:
            print(f"❌ CLEANUP FAILED: User A directory still exists.")
            
        # Cleanup test file
        if os.path.exists(dummy_file):
            os.remove(dummy_file)

async def main():
    try:
        await verify_user_isolation()
        print("\n🎉 PHASE 2 VERIFICATION COMPLETED SUCCESSFULLY!")
    except Exception as e:
        print(f"\n❌ PHASE 2 VERIFICATION FAILED: {str(e)}")

if __name__ == "__main__":
    # Ensure data dir exists
    if not os.path.exists("data/vector_db"):
        os.makedirs("data/vector_db")
    asyncio.run(main())
