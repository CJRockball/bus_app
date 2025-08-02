"""
Stockholm Bus Line 1 Countdown - FastAPI Version
Real-time bus tracking app with server-side rendering
Modified to show 2 departures per direction (4 total)
"""

import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
import httpx
from fastapi import FastAPI, Request, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import logging
from zoneinfo import ZoneInfo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for caching data
bus_data_cache = {
    "departures": [],
    "departures_by_direction": {},
    "last_updated": None,
    "error": None
}

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove disconnected connections
                if connection in self.active_connections:
                    self.active_connections.remove(connection)

manager = ConnectionManager()

# SL API Configuration - MODIFIED for 4 departures
SL_API_CONFIG = {
    "base_url": "https://transport.integration.sl.se/v1",
    "site_id": "1285",  # Stora Essingen
    "bus_line": "1",
    "max_departures": 6,  # Fetch more to ensure 2 per direction
    "departures_per_direction": 2,  # NEW: limit per direction
    "refresh_interval": 30  # seconds
}

# CORS proxies for handling CORS issues
CORS_PROXIES = [
    "https://api.allorigins.win/get?url=",
    "https://cors-anywhere.herokuapp.com/",
    "https://api.codetabs.com/v1/proxy?quest="
]

class BusDataFetcher:
    """Handles fetching and processing bus data from SL API"""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def fetch_departures(self) -> Dict:
        """Fetch departures with multiple fallback strategies"""
        api_url = f"{SL_API_CONFIG['base_url']}/sites/{SL_API_CONFIG['site_id']}/departures?transport=BUS&line=1&forecast=60"

        # Try direct API call first
        try:
            response = await self.client.get(api_url)
            if response.status_code == 200:
                data = response.json()
                return self.process_departure_data(data)
        except Exception as e:
            logger.warning(f"Direct API call failed: {e}")

        # Try CORS proxies
        for proxy in CORS_PROXIES:
            try:
                proxy_url = proxy + api_url
                response = await self.client.get(proxy_url)
                if response.status_code == 200:
                    # Handle different proxy response formats
                    if "allorigins" in proxy:
                        proxy_data = response.json()
                        data = json.loads(proxy_data["contents"])
                    else:
                        data = response.json()
                    return self.process_departure_data(data)
            except Exception as e:
                logger.warning(f"Proxy {proxy} failed: {e}")
                continue

        # Return mock data as fallback
        logger.info("Using mock data as fallback")
        return self.get_mock_data()

    def process_departure_data(self, data: Dict) -> Dict:
        """Process API response data - MODIFIED to group by direction"""
        try:
            all_departures = []
            if data and "departures" in data:
                for dep in data["departures"]:
                    line = dep.get("line", {})
                    if isinstance(line, dict):
                        line_designation = line.get("designation", "")
                    else:
                        line_designation = str(line)

                    if line_designation == SL_API_CONFIG["bus_line"]:
                        departure = {
                            "line": line_designation,
                            "destination": dep.get("destination", "Okänd destination"),
                            "expected_time": dep.get("expected") or dep.get("planned"),
                            "direction": dep.get("direction", ""),
                            "real_time": dep.get("expected") is not None
                        }
                        all_departures.append(departure)

            # Sort by expected time
            all_departures.sort(key=lambda x: x["expected_time"] or "")

            # Group by direction and limit to 2 per direction
            departures_by_direction = {}
            final_departures = []

            for departure in all_departures:
                direction = departure["direction"]
                if direction not in departures_by_direction:
                    departures_by_direction[direction] = []

                # Add to direction group if under limit
                if len(departures_by_direction[direction]) < SL_API_CONFIG["departures_per_direction"]:
                    departures_by_direction[direction].append(departure)
                    final_departures.append(departure)

                # Stop if we have enough total departures
                if len(final_departures) >= 4:
                    break

            return {
                "departures": final_departures,
                "departures_by_direction": departures_by_direction,
                "last_updated": datetime.now(tz=ZoneInfo('Europe/Stockholm')).isoformat(),
                "error": None,
                "source": "real_api"
            }
        except Exception as e:
            logger.error(f"Error processing departure data: {e}")
            return self.get_mock_data()

    def get_mock_data(self) -> Dict:
        """Generate mock data for demonstration - MODIFIED for 4 departures"""
        now = datetime.now(tz=ZoneInfo('Europe/Stockholm'))

        # Create 2 departures per direction
        mock_departures = [
            # Direction 1 (Frihamnen)
            {
                "line": "1",
                "destination": "Frihamnen",
                "expected_time": (now + timedelta(minutes=3)).isoformat(),
                "direction": "1",
                "real_time": True
            },
            {
                "line": "1",
                "destination": "Frihamnen", 
                "expected_time": (now + timedelta(minutes=8)).isoformat(),
                "direction": "1",
                "real_time": False
            },
            # Direction 2 (Stora Essingen)
            {
                "line": "1",
                "destination": "Stora Essingen",
                "expected_time": (now + timedelta(minutes=5)).isoformat(),
                "direction": "2",
                "real_time": True
            },
            {
                "line": "1",
                "destination": "Stora Essingen",
                "expected_time": (now + timedelta(minutes=12)).isoformat(),
                "direction": "2", 
                "real_time": False
            }
        ]

        # Group by direction
        departures_by_direction = {
            "1": [dep for dep in mock_departures if dep["direction"] == "1"],
            "2": [dep for dep in mock_departures if dep["direction"] == "2"]
        }

        return {
            "departures": mock_departures,
            "departures_by_direction": departures_by_direction,
            "last_updated": now.isoformat(),
            "error": "Using demonstration data - live API unavailable",
            "source": "mock_data"
        }

# Initialize bus data fetcher
bus_fetcher = BusDataFetcher()

# Background task for periodic data updates
async def update_bus_data():
    """Background task to update bus data periodically"""
    while True:
        try:
            logger.info("Updating bus data...")
            new_data = await bus_fetcher.fetch_departures()

            # Update global cache
            global bus_data_cache
            bus_data_cache.update(new_data)

            # Broadcast to WebSocket connections
            await manager.broadcast(json.dumps(new_data))

            logger.info(f"Bus data updated. Found {len(new_data['departures'])} departures")

        except Exception as e:
            logger.error(f"Error updating bus data: {e}")
            bus_data_cache["error"] = str(e)

        # Wait for next update
        await asyncio.sleep(SL_API_CONFIG["refresh_interval"])

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Stockholm Bus Countdown App...")

    # Start background task for data updates
    task = asyncio.create_task(update_bus_data())

    # Initial data fetch
    initial_data = await bus_fetcher.fetch_departures()
    bus_data_cache.update(initial_data)

    yield

    # Shutdown
    logger.info("Shutting down...")
    task.cancel()
    await bus_fetcher.client.aclose()

# Initialize FastAPI app
app = FastAPI(
    title="Stockholm Bus Line 1 Countdown",
    description="Real-time countdown for Stockholm bus line 1 from Stora Essingen - 2 per direction",
    version="2.1.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main page with server-side rendered HTML"""
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "initial_data": bus_data_cache,
            "config": SL_API_CONFIG
        }
    )

@app.get("/api/departures")
async def get_departures():
    """API endpoint for getting current departures"""
    return JSONResponse(bus_data_cache)

@app.post("/api/refresh")
async def refresh_departures(background_tasks: BackgroundTasks):
    """Manually refresh departure data"""
    async def refresh_task():
        global bus_data_cache
        new_data = await bus_fetcher.fetch_departures()
        bus_data_cache.update(new_data)
        await manager.broadcast(json.dumps(new_data))

    background_tasks.add_task(refresh_task)
    return {"message": "Refresh triggered"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)

    # Send current data immediately
    await websocket.send_text(json.dumps(bus_data_cache))

    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "last_updated": bus_data_cache.get("last_updated"),
        "active_connections": len(manager.active_connections),
        "total_departures": len(bus_data_cache.get("departures", [])),
        "departures_by_direction": {k: len(v) for k, v in bus_data_cache.get("departures_by_direction", {}).items()}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
