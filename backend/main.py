
from fastapi import FastAPI
from datetime import datetime, timedelta
from uuid import uuid4
import httpx
import os
app = FastAPI()
from dotenv import load_dotenv
load_dotenv()

CALENDLY_API_KEY = os.getenv('CALENDLY_API_KEY')
CALENDLY_USER_URL = os.getenv('CALENDLY_USER_URL')
USER_URI = os.getenv('USER_URI')
EVENT_TYPE_URI = os.getenv('EVENT_TYPE_URI')
CALENDLY_API_BASE = os.getenv('CALENDLY_API_BASE')

HEADERS = {
    "Authorization": f"Bearer {CALENDLY_API_KEY}",
    "Content-Type": "application/json",
}


@app.get("/user")
async def get_user_info():
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{CALENDLY_API_BASE}/users/me", headers=HEADERS)
        res.raise_for_status()
        return res.json()["resource"]


@app.get("/event_types")
async def get_event_types():
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{CALENDLY_API_BASE}/event_types", headers=HEADERS, params={"user": USER_URI})
        res.raise_for_status()
        return res.json()["collection"]


@app.get("/availability")
async def get_availability(start_date: str, end_date: str):
    start_iso = f"{start_date}T00:00:00Z"
    end_iso = f"{end_date}T23:59:59Z"

    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{CALENDLY_API_BASE}/event_type_available_times",
            headers=HEADERS,
            params={ "event_type": EVENT_TYPE_URI,"start_time": start_iso, "end_time": end_iso},
        )
        res.raise_for_status()
        data = res.json()

        slots = []
        for slot in data.get("collection", []):
            print(slot)
            start_time = datetime.fromisoformat(slot["start_time"].replace("Z", ""))
            slots.append({
                "start_time": slot["start_time"],
                "end_time": (start_time + timedelta(minutes=30)).isoformat() + "Z",
                "available": True,
            })

        return {"date_range": f"{start_date} - {end_date}", "available_slots": slots}


@app.post("/scheduled_events")
async def create_booking():
    booking_payload = {
        "max_event_count": 1,
        "owner": EVENT_TYPE_URI.strip('"').strip(),
        "owner_type": "EventType"  
    }

    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{CALENDLY_API_BASE}/scheduling_links",
            headers=HEADERS,
            json=booking_payload
        )

        res.raise_for_status()

    data = res.json()["resource"]

    return {
        "message": "✅ Booking link created successfully",
        "booking_url": data["booking_url"],
        "owner": data["owner"],
        "owner_type": data["owner_type"]
    }
