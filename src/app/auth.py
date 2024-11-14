# auth.py
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Security configurations
SECRET_KEY = "your-secret-key-here"  # Change this in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    node_id: Optional[str] = None

class NodeAuth(BaseModel):
    node_id: str
    secret: str

# Password context for hashing secrets
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_node(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        node_id: str = payload.get("sub")
        if node_id is None:
            raise credentials_exception
        token_data = TokenData(node_id=node_id)
    except JWTError:
        raise credentials_exception
    return token_data.node_id

def setup_auth_routes(app):
    # OAuth2 compatible token endpoint
    @app.post("/token", response_model=Token)
    async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
        # For testing, accept any username as node_id and "test" as password
        if form_data.password != "test":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": form_data.username},
            expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    # Alternative JSON endpoint for node authentication
    @app.post("/auth/token", response_model=Token)
    async def node_login(node_auth: NodeAuth):
        if node_auth.secret != "test":  # In production, validate against secure storage
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": node_auth.node_id},
            expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    @app.get("/protected-health")
    async def protected_health_check(current_node: str = Depends(get_current_node)):
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().timestamp(),
            "node_id": current_node
        }