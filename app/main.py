from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.models import TemperatureMeasurement, TemperatureMeasurementRequest, TemperatureMeasurementResponse
from app.auth import verify_credentials, _ensure_credentials_loaded, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from typing import List

# database imports
from app import db
from sqlalchemy import select

# Initialize FastAPI app
app = FastAPI(
    title="Temperature Measurements Service",
    description="REST API for submitting temperature measurements from sensors",
    version="1.0.0"
)

# In-memory storage deprecated; database will hold measurements
# keep typing annotation for reference
measurements_storage: List[TemperatureMeasurement] = []


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


@app.post("/api/measurements", response_model=TemperatureMeasurementResponse)
async def submit_measurements(
    request: TemperatureMeasurementRequest,
    credentials = Depends(verify_credentials)
):
    """
    Submit a list of temperature measurements from sensors.
    
    Args:
        request: TemperatureMeasurementRequest containing a list of measurements with:
            - sensorAddress: str - Unique identifier for the sensor
            - temperature: float - Temperature reading in Celsius
            - timestamp: datetime - Measurement timestamp
    
    Returns:
        TemperatureMeasurementResponse with status and count of received measurements
    """
    try:
        if not request.measurements:
            raise HTTPException(status_code=400, detail="No measurements provided")
        
        # persist measurements in database
        async with db.get_session() as session:
            for measurement in request.measurements:
                model = db.TemperatureMeasurementModel(
                    sensor_address=measurement.sensorAddress,
                    temperature=measurement.temperature,
                    timestamp=measurement.timestamp
                )
                session.add(model)
            await session.commit()

        return TemperatureMeasurementResponse(
            success=True,
            message=f"Successfully received {len(request.measurements)} temperature measurement(s)",
            measurements_received=len(request.measurements)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/measurements", response_model=List[TemperatureMeasurement])
async def get_measurements(credentials = Depends(verify_credentials)):
    """
    Retrieve all stored temperature measurements from the database.
    """
    async with db.get_session() as session:
        result = await session.execute(select(db.TemperatureMeasurementModel))
        rows = result.scalars().all()
    # convert to Pydantic models
    return [TemperatureMeasurement(
        sensorAddress=r.sensor_address,
        temperature=r.temperature,
        timestamp=r.timestamp
    ) for r in rows]


@app.get("/api/measurements/{sensor_address}")
async def get_sensor_measurements(
    sensor_address: str,
    credentials = Depends(verify_credentials)
):
    """
    Retrieve temperature measurements for a specific sensor.
    
    Args:
        sensor_address: Unique identifier for the sensor
    
    Returns:
        List of measurements for the specified sensor
    """
    async with db.get_session() as session:
        result = await session.execute(
            select(db.TemperatureMeasurementModel)
            .where(db.TemperatureMeasurementModel.sensor_address == sensor_address)
        )
        rows = result.scalars().all()

    if not rows:
        return {"error": f"No measurements found for sensor {sensor_address}", "data": []}

    measurements = [
        TemperatureMeasurement(
            sensorAddress=r.sensor_address,
            temperature=r.temperature,
            timestamp=r.timestamp
        ) for r in rows
    ]

    return {"sensor_address": sensor_address, "data": measurements}


@app.delete("/api/measurements")
async def clear_measurements(credentials = Depends(verify_credentials)):
    """Clear all stored measurements (for testing purposes)"""
    async with db.get_session() as session:
        result = await session.execute(select(db.TemperatureMeasurementModel))
        rows = result.scalars().all()
        count = len(rows)
        if count > 0:
            for row in rows:
                await session.delete(row)
            await session.commit()
    return {"message": f"Cleared {count} measurements"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
