from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import List
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from app.sensor import Sensor


class TemperatureMeasurement(BaseModel):
    """Model for a single temperature measurement"""
    sensorAddress: str
    temperature: float
    timestamp: datetime

    @field_validator('timestamp', mode='after')
    @classmethod
    def convert_timezone_aware_to_naive(cls, v):
        """Convert timezone-aware datetime to naive UTC datetime for database compatibility."""
        if isinstance(v, datetime) and v.tzinfo is not None:
            return v.replace(tzinfo=None)
        return v


class TemperatureMeasurementRequest(BaseModel):
    """Model for request containing a list of temperature measurements"""
    measurements: List[TemperatureMeasurement]


class TemperatureMeasurementResponse(BaseModel):
    """Model for response after processing measurements"""
    success: bool
    message: str
    measurements_received: int
