"""
database.py — Configuration de la connexion SQLAlchemy / PostgreSQL

Utilisé par le Documentation Agent (Feature 1) :
    context.md -> Parsing Agent -> Structured JSON
        -> Summary / Diagram / Glossary Agents
        -> Documentation Writer -> Design/Layout Agent
        -> Markdown/HTML -> PDF Generator

DATABASE_URL est lu depuis config.py (Pydantic-settings), centralisé et validé.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings  # <--- On importe les réglages centralisés

# Plus besoin de load_dotenv() ou d'os.environ ici, 
# la classe Settings de config.py gère déjà tout ça automatiquement !
DATABASE_URL = settings.DATABASE_URL

# pool_pre_ping évite les connexions mortes après une inactivité (utile en dev)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency FastAPI : fournit une session DB et la ferme proprement."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()