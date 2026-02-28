from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.models import TemperatureMeasurement, TemperatureMeasurementRequest, TemperatureMeasurementResponse
from app.auth import verify_credentials, _ensure_credentials_loaded
from typing import List

# Initialize FastAPI app
app = FastAPI(
    title="Temperature Measurements Service",
    description="REST API for submitting temperature measurements from sensors",
    version="1.0.0"
)

# In-memory storage for demonstrations (in production, use a database)
measurements_storage: List[TemperatureMeasurement] = []


@app.on_event("startup")
async def startup_event():
    """Verify credentials are configured on startup"""
    _ensure_credentials_loaded()


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
        
        # Process and store measurements
        for measurement in request.measurements:
            measurements_storage.append(measurement)
        
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
    Retrieve all stored temperature measurements.
    
    Returns:
        List of all temperature measurements stored in the service
    """
    return measurements_storage


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
    sensor_measurements = [
        m for m in measurements_storage 
        if m.sensorAddress == sensor_address
    ]
    
    if not sensor_measurements:
        return {"error": f"No measurements found for sensor {sensor_address}", "data": []}
    
    return {"sensor_address": sensor_address, "data": sensor_measurements}


@app.delete("/api/measurements")
async def clear_measurements(credentials = Depends(verify_credentials)):
    """Clear all stored measurements (for testing purposes)"""
    global measurements_storage
    count = len(measurements_storage)
    measurements_storage = []
    return {"message": f"Cleared {count} measurements"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
