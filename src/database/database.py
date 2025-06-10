from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional
from src.models.models import Base

class Database:
    def __init__(self, db_url: str = "sqlite:///data.db", echo: bool = False):
        self.engine = create_engine(db_url, echo=echo, future=True)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, future=True)
        self._session: Optional[Session] = None

    def get_session(self) -> Session:
        if self._session is None:
            self._session = self.SessionLocal()
        return self._session

    def close(self):
        if self._session is not None:
            self._session.close()
            self._session = None
