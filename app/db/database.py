from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import DATABASE_URL
from app.db.base import Base

class Database:
    def __init__(
        self,
        database_url: str | None = None,
    ) -> None:
        self.database_url = database_url or DATABASE_URL

        self.engine = create_engine(
            self.database_url,
        )

        self.session_factory = sessionmaker(
            bind=self.engine,
            class_=Session,
            expire_on_commit=False,
        )

    def create_session(self) -> Session:
        return self.session_factory()

    def create_tables(self) -> None:
        Base.metadata.create_all(
            self.engine
        )