"""
Módulo de autenticação para Mossify.

Fornece:
- Modelo User com email, senha hash, ativo, etc.
- Funções de hash e verificação (pbkdf2_sha256)
- Geração e validação de JWT
- Rotas /auth/register, /auth/login, /auth/me
- Fábrica create_get_current_user para gerar dependência com db_manager injetado
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import SQLModel, Field, Session, select

from .database import DatabaseManager

# ============================================
# Configurações (use variáveis de ambiente em produção)
# ============================================

SECRET_KEY = "your-secret-key-change-this"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ============================================
# Modelo User (criado automaticamente)
# ============================================


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================
# Hash e verificação
# ============================================

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ============================================
# JWT
# ============================================


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ============================================
# Dependência OAuth2
# ============================================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# ============================================
# Fábrica para get_current_user (com db_manager injetado)
# ============================================


def create_get_current_user(db_manager: DatabaseManager):
    """Retorna uma dependência get_current_user que usa o db_manager fornecido."""

    async def get_current_user(
        token: str = Depends(oauth2_scheme),
    ) -> User:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        with Session(db_manager.engine) as session:
            user = session.exec(select(User).where(User.email == email)).first()
            if user is None:
                raise credentials_exception
            return user

    return get_current_user


# ============================================
# Rotas de autenticação (registradas automaticamente)
# ============================================


def register_auth_routes(app, db_manager: DatabaseManager, prefix: str = "/auth"):
    """Registra as rotas de auth no FastAPI e retorna a dependência get_current_user."""

    # Cria a dependência get_current_user com o db_manager da aplicação
    get_current_user = create_get_current_user(db_manager)

    # Registrar usuário (público)
    @app.register_route(f"{prefix}/register", methods=["POST"])
    async def register(
        email: str,
        password: str,
        session: Session = Depends(db_manager.get_session),
    ):
        existing = session.exec(select(User).where(User.email == email)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        hashed = get_password_hash(password)
        user = User(email=email, hashed_password=hashed)
        session.add(user)
        session.commit()
        session.refresh(user)
        return {"id": user.id, "email": user.email, "message": "User created"}

    # Login (público) – compatível com OAuth2
    @app.register_route(f"{prefix}/login", methods=["POST"])
    async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        session: Session = Depends(db_manager.get_session),
    ):
        user = session.exec(
            select(User).where(User.email == form_data.username)
        ).first()
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect email or password")
        access_token = create_access_token(data={"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer"}

    # Obter usuário atual (protegido)
    @app.register_route(
        f"{prefix}/me", methods=["GET"], dependencies=[Depends(get_current_user)]
    )
    async def get_me(current_user: User = Depends(get_current_user)):
        return {
            "id": current_user.id,
            "email": current_user.email,
            "is_active": current_user.is_active,
        }

    return get_current_user
