"""
OpenWeatherMap integration for fetching external temperature measurements.
"""

import logging
import asyncio
import httpx
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import select

from app.db import get_session, TemperatureMeasurementModel, SensorModel

logger = logging.getLogger("app.weather")

# API Configuration
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"
WEATHER_SENSOR_ID = "api.openweathermap.org"
LATITUDE = 47.77625709979595
LONGITUDE = 9.152623862169138

# Interval for fetching weather data (in seconds)
FETCH_INTERVAL_SECONDS = 15 * 60  # 15 minutes


async def fetch_weather_temperature(api_key: str) -> float | None:
    """
    Fetch current temperature from OpenWeatherMap API.
    
    Args:
        api_key: OpenWeatherMap API key
        
    Returns:
        Temperature in Celsius, or None if fetch failed
    """
    try:
        params = {
            "lat": LATITUDE,
            "lon": LONGITUDE,
            "units": "metric",
            "appid": api_key
        }
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(WEATHER_API_URL, params=params)
            response.raise_for_status()
            
            data = response.json()
            temperature = data.get("main", {}).get("temp")
            
            if temperature is None:
                logger.warning("Temperature data not found in API response")
                return None
                
            logger.info(f"Fetched temperature from OpenWeatherMap: {temperature}°C")
            return temperature
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching weather: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching weather: {e}")
        return None


async def store_temperature_measurement(temperature: float) -> bool:
    """
    Store temperature measurement in database.
    
    Args:
        temperature: Temperature value in Celsius
        
    Returns:
        True if successful, False otherwise
    """
    try:
        async with get_session() as session:
            # Ensure sensor exists
            result = await session.execute(
                select(SensorModel).where(SensorModel.sensorAddress == WEATHER_SENSOR_ID)
            )
            sensor = result.scalar_one_or_none()
            
            if not sensor:
                sensor = SensorModel(
                    sensorAddress=WEATHER_SENSOR_ID,
                    active=True,
                    color="",
                    name="OpenWeatherMap External Temperature",
                    groupName="External",
                    linetype=""
                )
                session.add(sensor)
                await session.flush()
                logger.info(f"Created new sensor: {WEATHER_SENSOR_ID}")
            
            # Create measurement
            measurement = TemperatureMeasurementModel(
                sensor_address=WEATHER_SENSOR_ID,
                temperature=temperature,
                timestamp=datetime.now(ZoneInfo("Europe/Berlin")).replace(tzinfo=None)
            )
            session.add(measurement)
            await session.commit()
            
            logger.info(f"Stored temperature measurement: {temperature}°C at {measurement.timestamp}")
            return True
            
    except Exception as e:
        logger.error(f"Error storing temperature measurement: {e}")
        return False


async def weather_fetch_task(api_key: str):
    """
    Background task that periodically fetches weather data and stores it.
    
    Args:
        api_key: OpenWeatherMap API key
    """
    logger.info(f"Starting weather fetch task (interval: {FETCH_INTERVAL_SECONDS//60} minutes)")
    
    while True:
        try:
            # Fetch temperature
            temperature = await fetch_weather_temperature(api_key)
            
            if temperature is not None:
                # Store in database
                await store_temperature_measurement(temperature)
            else:
                logger.warning("No temperature data fetched, skipping storage")
            
            # Wait for next fetch
            await asyncio.sleep(FETCH_INTERVAL_SECONDS)
            
        except Exception as e:
            logger.error(f"Unexpected error in weather fetch task: {e}")
            # Continue with next iteration after a short delay
            await asyncio.sleep(FETCH_INTERVAL_SECONDS)
