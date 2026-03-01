from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.models import TemperatureMeasurement, TemperatureMeasurementRequest, TemperatureMeasurementResponse
from app.db import get_session, TemperatureMeasurementModel, SensorModel
from app.auth import verify_credentials, _ensure_credentials_loaded, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from typing import Dict, List
from pydantic import BaseModel, field_validator
from app.db import get_session, TemperatureMeasurementModel, SensorModel

# database imports
from app import db
from sqlalchemy import select
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from datetime import date, datetime, timedelta

# Pydantic Modelle für Messungen
class TemperatureMeasurementCreate(BaseModel):
    sensor_address: str
    temperature: float
    timestamp: datetime

    @field_validator('timestamp', mode='after')
    @classmethod
    def convert_timezone_aware_to_naive(cls, v):
        """Convert timezone-aware datetime to naive UTC datetime for database compatibility."""
        if isinstance(v, datetime) and v.tzinfo is not None:
            return v.replace(tzinfo=None)
        return v

class TemperatureMeasurementRead(TemperatureMeasurementCreate):
    id: int


class MeasurementItem(BaseModel):
    temperature: float
    timestamp: datetime

    @field_validator('timestamp', mode='after')
    @classmethod
    def convert_timezone_aware_to_naive(cls, v):
        """Convert timezone-aware datetime to naive UTC datetime for database compatibility."""
        if isinstance(v, datetime) and v.tzinfo is not None:
            return v.replace(tzinfo=None)
        return v


class SensorDayMeasurements(BaseModel):
    sensor_address: str
    measurements: List[MeasurementItem]

# Pydantic Modelle für Sensoren
class SensorCreate(BaseModel):
    sensorAddress: str
    active: bool = True
    color: str = ""
    name: str = ""
    groupName: str = ""

class SensorRead(SensorCreate):
    pass

# Initialize FastAPI app
app = FastAPI(
    title="Temperature Measurements Service",
    description="REST API for submitting temperature measurements from sensors",
    version="1.0.0"
)

# In-memory storage deprecated; database will hold measurements
# keep typing annotation for reference
measurements_storage: List[TemperatureMeasurementRead] = []


@app.on_event("startup")
async def startup_event():
    """Verify credentials and initialize database on startup"""
    _ensure_credentials_loaded()
    # Ensure database configuration is available
    if not all([DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD]):
        raise RuntimeError("Database configuration missing in properties file")
    # build connection URL and initialize engine
    url = db.get_connection_url(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
    db.init_engine(url)
    await db.create_tables()


@app.get("/")
async def root():
    """Health check endpoint (no authentication required)"""
    return {
        "service": "Temperature Measurements Service",
        "status": "running",
        "version": "1.0.0"
    }


@app.post("/api/measurements", response_model=TemperatureMeasurementRead)
async def create_measurement(measurement: TemperatureMeasurementCreate, credentials=Depends(verify_credentials)):
    """Submit a temperature measurement from a sensor. Creates sensor if it doesn't exist."""
    async with get_session() as session:
        # Ensure sensor exists, create if necessary
        result = await session.execute(
            select(SensorModel).where(SensorModel.sensorAddress == measurement.sensor_address)
        )
        sensor = result.scalar_one_or_none()
        if not sensor:
            sensor = SensorModel(
                sensorAddress=measurement.sensor_address,
                active=True,
                color="",
                name="",
                groupName=""
            )
            session.add(sensor)
            await session.flush()
        
        # Create and store measurement
        db_measurement = TemperatureMeasurementModel(**measurement.dict())
        session.add(db_measurement)
        await session.commit()
        await session.refresh(db_measurement)
        return db_measurement


@app.post("/api/measurements/batch", response_model=TemperatureMeasurementResponse)
async def create_measurements_batch(request: TemperatureMeasurementRequest, credentials=Depends(verify_credentials)):
    """Submit a batch of temperature measurements from one or more sensors. Creates sensors if they don't exist."""
    async with get_session() as session:
        count = 0
        for measurement in request.measurements:
            # Ensure sensor exists, create if necessary
            result = await session.execute(
                select(SensorModel).where(SensorModel.sensorAddress == measurement.sensorAddress)
            )
            sensor = result.scalar_one_or_none()
            if not sensor:
                sensor = SensorModel(
                    sensorAddress=measurement.sensorAddress,
                    active=True,
                    color="",
                    name="",
                    groupName=""
                )
                session.add(sensor)
                await session.flush()
            
            # Create and store measurement
            db_measurement = TemperatureMeasurementModel(
                sensor_address=measurement.sensorAddress,
                temperature=measurement.temperature,
                timestamp=measurement.timestamp
            )
            session.add(db_measurement)
            count += 1
        
        await session.commit()
        
        return TemperatureMeasurementResponse(
            success=True,
            message=f"Successfully received {count} temperature measurement(s)",
            measurements_received=count
        )


@app.get("/api/measurements", response_model=List[TemperatureMeasurementRead])
async def list_measurements(credentials=Depends(verify_credentials)):
    """Retrieve all stored temperature measurements from the database."""
    async with get_session() as session:
        result = await session.execute(select(TemperatureMeasurementModel))
        measurements = result.scalars().all()
        return measurements


@app.get("/api/measurements/day/{target_date}", response_model=List[SensorDayMeasurements])
async def list_measurements_by_day(target_date: date, credentials=Depends(verify_credentials)):
    """Retrieve all temperature measurements for a given day, grouped by sensor address."""
    day_start = datetime.combine(target_date, datetime.min.time())
    day_end = day_start + timedelta(days=1)

    async with get_session() as session:
        result = await session.execute(
            select(TemperatureMeasurementModel)
            .where(TemperatureMeasurementModel.timestamp >= day_start)
            .where(TemperatureMeasurementModel.timestamp < day_end)
            .order_by(TemperatureMeasurementModel.sensor_address, TemperatureMeasurementModel.timestamp)
        )
        measurements = result.scalars().all()

    grouped: Dict[str, List[MeasurementItem]] = {}
    for measurement in measurements:
        grouped.setdefault(measurement.sensor_address, []).append(
            MeasurementItem(
                temperature=measurement.temperature,
                timestamp=measurement.timestamp,
            )
        )

    return [
        SensorDayMeasurements(sensor_address=sensor_address, measurements=entries)
        for sensor_address, entries in grouped.items()
    ]


@app.get("/api/measurements/{measurement_id}", response_model=TemperatureMeasurementRead)
async def get_measurement(measurement_id: int, credentials=Depends(verify_credentials)):
    """Retrieve a specific temperature measurement."""
    async with get_session() as session:
        result = await session.execute(
            select(TemperatureMeasurementModel).where(TemperatureMeasurementModel.id == measurement_id)
        )
        measurement = result.scalar_one_or_none()
        if not measurement:
            raise HTTPException(status_code=404, detail="Measurement not found")
        return measurement


@app.put("/api/measurements/{measurement_id}", response_model=TemperatureMeasurementRead)
async def update_measurement(measurement_id: int, measurement: TemperatureMeasurementCreate, credentials=Depends(verify_credentials)):
    """Update a specific temperature measurement."""
    async with get_session() as session:
        result = await session.execute(
            select(TemperatureMeasurementModel).where(TemperatureMeasurementModel.id == measurement_id)
        )
        db_measurement = result.scalar_one_or_none()
        if not db_measurement:
            raise HTTPException(status_code=404, detail="Measurement not found")
        for key, value in measurement.dict().items():
            setattr(db_measurement, key, value)
        await session.commit()
        await session.refresh(db_measurement)
        return db_measurement


@app.delete("/api/measurements/{measurement_id}")
async def delete_measurement(measurement_id: int, credentials=Depends(verify_credentials)):
    """Clear all stored measurements (for testing purposes)"""
    async with get_session() as session:
        result = await session.execute(
            select(TemperatureMeasurementModel).where(TemperatureMeasurementModel.id == measurement_id)
        )
        db_measurement = result.scalar_one_or_none()
        if not db_measurement:
            raise HTTPException(status_code=404, detail="Measurement not found")
        await session.delete(db_measurement)
        await session.commit()
        return {"success": True}


@app.delete("/api/sensors/{sensorAddress}")
async def delete_sensor(sensorAddress: str, credentials=Depends(verify_credentials)):
    async with get_session() as session:
        result = await session.execute(select(SensorModel).where(SensorModel.sensorAddress == sensorAddress))
        db_sensor = result.scalar_one_or_none()
        if not db_sensor:
            raise HTTPException(status_code=404, detail="Sensor not found")
        await session.delete(db_sensor)
        await session.commit()
        return {"success": True}

@app.post("/api/sensors", response_model=SensorRead)
async def create_sensor(sensor: SensorCreate, credentials=Depends(verify_credentials)):
    async with get_session() as session:
        db_sensor = SensorModel(**sensor.dict())
        session.add(db_sensor)
        await session.commit()
        await session.refresh(db_sensor)
        return db_sensor

@app.get("/api/sensors", response_model=List[SensorRead])
async def list_sensors(credentials=Depends(verify_credentials)):
    async with get_session() as session:
        result = await session.execute(select(SensorModel))
        sensors = result.scalars().all()
        return sensors

@app.get("/api/sensors/{sensorAddress}", response_model=SensorRead)
async def get_sensor(sensorAddress: str, credentials=Depends(verify_credentials)):
    async with get_session() as session:
        result = await session.execute(select(SensorModel).where(SensorModel.sensorAddress == sensorAddress))
        sensor = result.scalar_one_or_none()
        if not sensor:
            raise HTTPException(status_code=404, detail="Sensor not found")
        return sensor

@app.put("/api/sensors/{sensorAddress}", response_model=SensorRead)
async def update_sensor(sensorAddress: str, sensor: SensorCreate, credentials=Depends(verify_credentials)):
    async with get_session() as session:
        result = await session.execute(select(SensorModel).where(SensorModel.sensorAddress == sensorAddress))
        db_sensor = result.scalar_one_or_none()
        if not db_sensor:
            raise HTTPException(status_code=404, detail="Sensor not found")
        for key, value in sensor.dict().items():
            setattr(db_sensor, key, value)
        await session.commit()
        await session.refresh(db_sensor)
        return db_sensor

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
