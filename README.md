# Stockholm Bus Line 1 Countdown - FastAPI Version

A real-time bus tracking application for Stockholm's bus line 1 from Stora Essingen station, built with FastAPI, WebSockets, and server-side rendering.

## Features

- **Real-time Updates**: WebSocket-based live data updates
- **Server-side Rendering**: Fast initial page loads using Jinja2 templates
- **Multiple API Fallbacks**: Handles CORS issues with proxy servers and mock data
- **Responsive Design**: Mobile-optimized interface with SL branding
- **Background Tasks**: Automatic data refresh every 30 seconds
- **Connection Management**: WebSocket connection status and auto-reconnect
- **Manual Refresh**: User-initiated data refresh capability

## Installation

1. Clone or download the project files
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the FastAPI development server:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Open your browser and navigate to:
   - **Main App**: http://localhost:8000
   - **API Docs**: http://localhost:8000/docs
   - **Health Check**: http://localhost:8000/health

## API Endpoints

- `GET /` - Main HTML page with real-time countdown
- `GET /api/departures` - JSON API for current departures
- `POST /api/refresh` - Trigger manual data refresh
- `WS /ws` - WebSocket endpoint for real-time updates
- `GET /health` - Health check endpoint

## Architecture

### Backend (FastAPI)
- **Background Tasks**: Periodic SL API calls using asyncio
- **WebSocket Manager**: Handles real-time client connections
- **Data Fetcher**: Multiple fallback strategies for API access
- **Template Rendering**: Server-side HTML generation with Jinja2

### Frontend (HTML/CSS/JavaScript)
- **WebSocket Client**: Real-time data consumption
- **Countdown Timers**: Live MM:SS format countdown displays
- **Connection Status**: Visual indicators for WebSocket state
- **Responsive Design**: Mobile-first CSS with SL brand colors

### Data Flow
1. Background task fetches SL API data every 30 seconds
2. New data is cached and broadcast via WebSockets
3. Connected clients receive updates and refresh UI
4. Manual refresh triggers immediate API call

## Configuration

Edit the `SL_API_CONFIG` in `main.py` to customize:
- `site_id`: SL site ID (default: 740024924 for Stora Essingen)
- `bus_line`: Bus line number (default: "1")
- `max_departures`: Number of departures to show (default: 2)
- `refresh_interval`: Update frequency in seconds (default: 30)

## Production Deployment

For production deployment, consider:

1. **Using Gunicorn**:
   ```bash
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

2. **Environment Variables**:
   - Set `PYTHONPATH` for module imports
   - Configure logging levels
   - Set up proper error monitoring

3. **Reverse Proxy**:
   - Use Nginx or similar for static file serving
   - Configure WebSocket proxy settings
   - Set up SSL/TLS certificates

## Troubleshooting

### CORS Issues
The app includes multiple fallback strategies for CORS issues:
1. Direct SL API access (preferred)
2. CORS proxy services (allorigins.win, cors-anywhere.herokuapp.com)
3. Mock data (demonstration purposes)

### WebSocket Connection Issues
- Check firewall settings for WebSocket connections
- Ensure proxy servers support WebSocket upgrades
- Monitor browser console for connection errors

### Performance
- Monitor active WebSocket connections via `/health` endpoint
- Consider connection limits for production deployment
- Use Redis for session management with multiple workers

## License

This project is for educational and demonstration purposes. SL (Storstockholms Lokaltrafik) data is used according to their terms of service.
