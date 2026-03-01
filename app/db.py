from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime
from typing import List

# Base class for declarative models
Base = declarative_base()

class SensorModel(Base):
    __tablename__ = "sensors"
    sensorAddress = Column(String, primary_key=True, index=True)
    active = Column(Boolean, default=True)
    color = Column(String)
    name = Column(String)
    groupName = Column(String)


from sqlalchemy import ForeignKey

class TemperatureMeasurementModel(Base):
    __tablename__ = "temperature_measurements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_address = Column(String, ForeignKey("sensors.sensorAddress"), nullable=False)
    temperature = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)


# global engine and session factory will be initialized at startup
_engine: AsyncEngine | None = None
_session_factory: sessionmaker | None = None


def get_connection_url(host: str, port: int, dbname: str, user: str, password: str) -> str:
    # using asyncpg
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}"


def init_engine(url: str):
    global _engine, _session_factory
    _engine = create_async_engine(url, echo=False)
    _session_factory = sessionmaker(
        _engine, class_=AsyncSession, expire_on_commit=False
    )


def get_session() -> AsyncSession:
    if _session_factory is None:
        raise RuntimeError("Database engine not initialized")
    return _session_factory()


async def create_tables():
    if _engine is None:
        raise RuntimeError("Database engine not initialized")
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
