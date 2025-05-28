from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.models.database import get_db, User, SessionToken, UserProfile
from app.models.schemas import UserRegister, UserLogin, AuthResponse, UserResponse
from app.config import get_settings
import hashlib
import secrets
import logging
from datetime import datetime, timedelta

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

class AuthService:
    """Core authentication service with secure password handling and session management"""
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> tuple[str, str]:
        """Hash password using PBKDF2 with salt"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        # Use PBKDF2 with SHA256
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # 100,000 iterations
        )
        return password_hash.hex(), salt
    
    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        """Verify password against stored hash"""
        try:
            # Extract salt and hash from stored format: salt:hash
            if ':' in stored_hash:
                salt, hash_value = stored_hash.split(':', 1)
                computed_hash, _ = AuthService.hash_password(password, salt)
                return computed_hash == hash_value
            return False
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    @staticmethod
    def generate_user_id() -> str:
        """Generate unique user_id compatible with existing AI system"""
        return f"user_{secrets.token_hex(16)}"
    
    @staticmethod
    def generate_session_token() -> str:
        """Generate cryptographically secure session token"""
        return secrets.token_urlsafe(64)
    
    @staticmethod
    def create_session_token(user_id: str, db: Session) -> tuple[str, datetime]:
        """Create new session token with expiration"""
        token = AuthService.generate_session_token()
        expires_at = datetime.utcnow() + timedelta(days=30)  # 30-day expiration
        
        # Clean up old tokens for this user
        db.query(SessionToken).filter(SessionToken.user_id == user_id).delete()
        
        # Create new token
        session_token = SessionToken(
            token=token,
            user_id=user_id,
            expires_at=expires_at
        )
        db.add(session_token)
        db.commit()
        
        return token, expires_at

def extract_token_from_request(request: Request) -> str:
    """Extract authentication token from request"""
    # Try Authorization header first
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        return authorization.split("Bearer ")[1]
    
    # Try query parameter as fallback
    token = request.query_params.get("token")
    if token:
        return token
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication token required"
    )

async def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency to get current authenticated user from session token"""
    try:
        token = extract_token_from_request(request)
        
        # Find valid session token
        session_token = db.query(SessionToken).filter(
            SessionToken.token == token,
            SessionToken.expires_at > datetime.utcnow()
        ).first()
        
        if not session_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        # Get user
        user = db.query(User).filter(
            User.user_id == session_token.user_id,
            User.is_active == True
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

@router.post("/register", response_model=AuthResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user and create their AI profile"""
    try:
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists (if provided)
        if user_data.email:
            existing_email = db.query(User).filter(User.email == user_data.email).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # Generate unique user_id for AI system
        user_id = AuthService.generate_user_id()
        
        # Hash password securely
        password_hash, salt = AuthService.hash_password(user_data.password)
        stored_hash = f"{salt}:{password_hash}"
        
        # Create authentication user
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=stored_hash,
            user_id=user_id,
            display_name=user_data.display_name or user_data.username
        )
        db.add(new_user)
        db.flush()  # Get the user ID
        
        # Create AI profile for personalization
        user_profile = UserProfile(
            user_id=user_id,
            name=user_data.display_name or user_data.username,
            preferences={},
            interests=[],
            communication_style={"formality": "balanced", "verbosity": "moderate"}
        )
        db.add(user_profile)
        
        # Create session token
        token, expires_at = AuthService.create_session_token(user_id, db)
        
        # Calculate expires_in seconds
        expires_in = int((expires_at - datetime.utcnow()).total_seconds())
        
        logger.info(f"New user registered: {user_data.username} with user_id: {user_id}")
        
        return AuthResponse(
            access_token=token,
            user=UserResponse(
                id=new_user.id,
                username=new_user.username,
                email=new_user.email,
                display_name=new_user.display_name,
                user_id=new_user.user_id,
                is_active=new_user.is_active,
                created_at=new_user.created_at
            ),
            expires_in=expires_in
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=AuthResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and create session token"""
    try:
        # Find user by username
        user = db.query(User).filter(User.username == credentials.username).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Verify password
        if not AuthService.verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Create session token
        token, expires_at = AuthService.create_session_token(user.user_id, db)
        
        # Calculate expires_in seconds
        expires_in = int((expires_at - datetime.utcnow()).total_seconds())
        
        logger.info(f"User logged in: {user.username}")
        
        return AuthResponse(
            access_token=token,
            user=UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                display_name=user.display_name,
                user_id=user.user_id,
                is_active=user.is_active,
                created_at=user.created_at
            ),
            expires_in=expires_in
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    """Invalidate session token"""
    try:
        token = extract_token_from_request(request)
        
        # Remove session token
        deleted_count = db.query(SessionToken).filter(SessionToken.token == token).delete()
        db.commit()
        
        if deleted_count > 0:
            logger.info("User logged out successfully")
            return {"message": "Logged out successfully"}
        else:
            return {"message": "Token not found or already expired"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        display_name=current_user.display_name,
        user_id=current_user.user_id,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    ) 