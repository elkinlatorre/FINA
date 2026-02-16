import asyncio
import os
import jwt
import sys
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from psycopg_pool import AsyncConnectionPool

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Load environment variables from the orchestrator .env
load_dotenv("../fina-orchestrator/.env")

async def test_postgres_connection():
    db_url = os.getenv("SUPABASE_DB_URL")
    if not db_url:
        print("❌ Error: SUPABASE_DB_URL not found in .env")
        return False
    
    print(f"🔗 Attempting to connect to Postgres...")
    try:
        async with AsyncConnectionPool(conninfo=db_url, min_size=0, max_size=1) as pool:
            async with pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT 1")
                    result = await cur.fetchone()
                    if result[0] == 1:
                        print("✅ Postgres Connection: SUCCESS")
                        return True
    except Exception as e:
        print(f"❌ Postgres Connection: FAILED - {str(e)}")
        return False

def test_jwt_logic():
    secret = os.getenv("JWT_SECRET", "super-secret-key-change-me")
    algo = "HS256"
    user_id = "test_user_v1"
    
    print(f"🔑 Testing JWT Logic...")
    try:
        # Encode
        payload = {
            "sub": user_id,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=60)
        }
        token = jwt.encode(payload, secret, algorithm=algo)
        print(f"✅ Token Generation: SUCCESS")
        
        # Decode
        decoded = jwt.decode(token, secret, algorithms=[algo])
        if decoded.get("sub") == user_id:
            print(f"✅ Token Validation: SUCCESS (User: {decoded.get('sub')})")
            return True
        else:
            print("❌ Token Validation: FAILED - User ID mismatch")
            return False
    except Exception as e:
        print(f"❌ JWT Logic: FAILED - {str(e)}")
        return False

async def main():
    print("--- FINA Phase 1 Verification ---")
    pg_ok = await test_postgres_connection()
    jwt_ok = test_jwt_logic()
    
    if pg_ok and jwt_ok:
        print("\n🎉 PHASE 1 VERIFICATION COMPLETED SUCCESSFULLY!")
    else:
        print("\n⚠️ PHASE 1 VERIFICATION FAILED. Please check your .env variables.")

if __name__ == "__main__":
    asyncio.run(main())
