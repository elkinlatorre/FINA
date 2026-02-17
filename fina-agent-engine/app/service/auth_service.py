import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.settings import settings
from app.core.logger import get_logger

logger = get_logger("AUTH_SERVICE")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

from jwt import PyJWKClient

class AuthService:
    def __init__(self):
        self._jwks_client = None
        logger.info("AuthService instance created")

    def _get_jwks_client(self):
        """Lazy initialization of JWKS client to ensure settings are loaded."""
        if self._jwks_client is not None:
            return self._jwks_client
        
        if settings.SUPABASE_URL:
            # Standard Supabase JWKS endpoint
            jwks_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
            masked_url = f"{settings.SUPABASE_URL[:12]}...{settings.SUPABASE_URL[-5:]}"
            logger.info(f"🔄 Attempting to initialize JWKS Client for: {masked_url}")
            try:
                self._jwks_client = PyJWKClient(jwks_url)
                logger.info(f"✅ JWKS Client successfully initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize JWKS Client: {e}")
        else:
            logger.warning("⚠️ SUPABASE_URL not set, JWKS won't be available for asymmetric tokens")
            
        return self._jwks_client

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Creates a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt

    async def get_current_user(self, token: str = Depends(oauth2_scheme)):
        """Validates the JWT token and returns user information."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            # First, peek at the header to determine the algorithm
            unverified_header = jwt.get_unverified_header(token)
            alg = unverified_header.get("alg", "HS256")
            
            # Get JWKS client lazily
            jwks_client = self._get_jwks_client()
            
            # Use JWKS for asymmetric algorithms (RS..., ES...)
            if alg.startswith(("RS", "ES")) and jwks_client:
                logger.debug(f"Verifying asymmetric token with algorithm {alg} using JWKS")
                signing_key = jwks_client.get_signing_key_from_jwt(token)
                key = signing_key.key
            else:
                # Fallback to symmetric secret for HS...
                logger.debug(f"Verifying symmetric token with algorithm {alg} using secret")
                key = settings.JWT_SECRET

            payload = jwt.decode(
                token, 
                key, 
                algorithms=["HS256", "RS256", "ES256", "HS384", "HS512", "ES384", "ES512"],
                audience="authenticated",
                leeway=60
            )
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
            return {"user_id": user_id}
        except Exception as e:
            unverified_header = {}
            try:
                unverified_header = jwt.get_unverified_header(token)
            except:
                pass
            
            error_msg = f"JWT Validation error: {str(e)} | Token Alg: {unverified_header.get('alg')} | " \
                        f"SupabaseURL: {settings.SUPABASE_URL[:10]}... | SecretLen: {len(settings.JWT_SECRET)}"
            logger.error(error_msg)
            raise credentials_exception

auth_service = AuthService()
