from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timezone
import os

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Initialize FastAPI
app = FastAPI(
    title="ROOT SENSE API",
    description="IoT-based Smart Agriculture System",
    version="1.0"
)

# Connect to Supabase
supabase = None

if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# Sensor data validation
class SensorData(BaseModel):
    device_id: str = "ROOTSENSE_001"
    temperature: float = Field(ge=-10, le=70)
    humidity: float = Field(ge=0, le=100)
    soil_moisture: float = Field(ge=0, le=100)


# Home endpoint
@app.get("/")
def home():
    return {
        "message": "ROOT SENSE Backend is Running!",
        "status": "Online",
        "database": "Connected" if supabase else "Not configured"
    }


# Receive and save sensor data
@app.post("/sensor-data")
def receive_sensor_data(data: SensorData):

    if supabase is None:
        raise HTTPException(
            status_code=503,
            detail="Supabase is not configured"
        )

    irrigation_status = (
        "WATER NEEDED"
        if data.soil_moisture < 30
        else "SOIL MOISTURE OK"
    )

    record = {
        "device_id": data.device_id,
        "temperature": data.temperature,
        "humidity": data.humidity,
        "soil_moisture": data.soil_moisture,
        "recorded_at": datetime.now(timezone.utc).isoformat()
    }

    try:
        result = (
            supabase.table("sensor_readings")
            .insert(record)
            .execute()
        )

        return {
            "message": "Sensor data saved successfully",
            "database_status": "Saved",
            "irrigation_status": irrigation_status,
            "data": record
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get latest sensor reading
@app.get("/sensor-data/latest")
def get_latest_sensor_data():

    if supabase is None:
        raise HTTPException(
            status_code=503,
            detail="Supabase is not configured"
        )

    try:
        result = (
            supabase.table("sensor_readings")
            .select("*")
            .order("recorded_at", desc=True)
            .limit(1)
            .execute()
        )

        return {"latest_reading": result.data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get sensor history
@app.get("/sensor-data/history")
def get_sensor_history():

    if supabase is None:
        raise HTTPException(
            status_code=503,
            detail="Supabase is not configured"
        )

    try:
        result = (
            supabase.table("sensor_readings")
            .select("*")
            .order("recorded_at", desc=True)
            .limit(100)
            .execute()
        )

        return {"readings": result.data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
