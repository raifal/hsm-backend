from pydantic import BaseModel
from datetime import datetime
from typing import List


class TemperatureMeasurement(BaseModel):
    """Model for a single temperature measurement"""
    sensorAddress: str
    temperature: float
    timestamp: datetime


class TemperatureMeasurementRequest(BaseModel):
    """Model for request containing a list of temperature measurements"""
    measurements: List[TemperatureMeasurement]


class TemperatureMeasurementResponse(BaseModel):
    """Model for response after processing measurements"""
    success: bool
    message: str
    measurements_received: int
