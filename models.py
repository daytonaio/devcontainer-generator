from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class DevContainer(Base):
    __tablename__ = "devcontainers"

    id = Column(Integer, primary_key=True)
    url = Column(String, index=True)
    devcontainer_json = Column(Text)
    repo_context = Column(Text)
    tokens = Column(Integer)
    model = Column(Text)
    embedding = Column(Text)
    generated = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))