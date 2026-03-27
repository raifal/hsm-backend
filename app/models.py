from pydantic import BaseModel
from typing import List
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class TemperatureMeasurement(BaseModel):
    """Model for a single temperature measurement"""
    sensorAddress: str
    temperature: float


class TemperatureMeasurementRequest(BaseModel):
    """Model for request containing a list of temperature measurements"""
    measurements: List[TemperatureMeasurement]


class TemperatureMeasurementResponse(BaseModel):
    """Model for response after processing measurements"""
    success: bool
    message: str
    measurements_received: int
