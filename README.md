#     Cam's Weather Fetcher - TravelBlog_WeatherAPI

A Flask-based weather API integration that helps travel bloggers exploring England get accurate, up-to-date weather information for their journey.

##    Project Overview

This app was built for my COS60016: Programming for Development assignment at Swinburne University. It grabs real-time weather data from OpenWeatherMap and presents it in a user-friendly format for travel bloggers who need accurate weather updates for their England trip.

## ✨ Features

- 🗺️ **Interactive Maps** showing all locations with weather overlays
- 📊 **Comprehensive Dashboard** with sortable and searchable weather cards
- 📱 **Responsive Design** that works on all devices
- 🔄 **Async API Calls** for blazing fast performance
- 💾 **Response Caching** to reduce API calls and improve load times
- 🛡️ **Error Handling** for API failures, rate limits, and invalid inputs
- 📈 **Data Visualization** with interactive charts for weather comparison

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- OpenWeatherMap API key (get one at [OpenWeatherMap](https://openweathermap.org/api))

### Installation

1. Clone this repo:
   ```bash
   git clone https://github.com/0x1049678II/TravelBlog_WeatherAPI.git
   cd TravelBlog_WeatherAPI
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your API key:
   ```
   OPENWEATHERMAP_API_KEY=your_api_key_here
   DEBUG=False
   ```

5. Run the app:
   ```bash
   python main.py
   ```

6. Open your browser and go to:
   ```
   http://127.0.0.1:5000
   ```

## 📋 Project Structure

```
TravelBlog_WeatherAPI/
├── models/               # Data models
│   └── weather.py        # Weather data representation
├── services/             # Service layer
│   └── api_client.py     # OpenWeatherMap API client
├── static/               # Static assets
│   ├── css/              # Stylesheets
│   ├── images/           # Images
│   └── js/               # JavaScript files
├── templates/            # HTML templates
│   ├── about.html        # About page
│   ├── base.html         # Base template
│   ├── dashboard.html    # Weather dashboard
│   ├── error.html        # Error page
│   ├── index.html        # Home page
│   └── weather.html      # Location weather details
├── tests/                # Unit tests
├── .env                  # Environment variables
├── app.py                # Flask application
├── config.py             # Configuration settings
├── main.py               # Application entry point
└── requirements.txt      # Dependencies
```

## 🔌 API Endpoints

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `/api/weather/:location_name` | Get weather for a location | `location_name`: Name of location |
| `/api/weather/all` | Get weather for all locations | None |

## 💡 Implementation Highlights

### Asynchronous API Calls
I've implemented async/await to fetch weather for all locations concurrently, which makes the dashboard load way faster.

```python
async def get_all_locations_weather_async(self):
    # Concurrent API requests
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_location_weather(session, location) for location in Config.LOCATIONS]
        # ...
```

### Caching for Performance
I've added a caching decorator to store API responses and reduce redundant API calls:

```python
@cache_response(timeout=Config.CACHE_TIMEOUT)
def get_current_weather(self, lat, lon):
    # This function's results will be cached
```

### Error Handling
Comprehensive error handling for all kinds of failures:

```python
try:
    # API request
except RequestException as e:
    raise ConnectionError(f"Failed to connect to API: {str(e)}")
except json.JSONDecodeError as e:
    raise ResponseParsingError(f"Failed to parse API response: {str(e)}")
```

##   Technologies Used

- **Python** for backend logic
- **Flask** for web framework
- **OpenWeatherMap API** for weather data
- **Bootstrap** for frontend styling
- **Leaflet.js** for interactive maps
- **Chart.js** for data visualization
- **aiohttp** for async API calls
- **Jinja2** for HTML templating

##   Notes

This app disables SSL verification for development to work around macOS certificate issues. In a production environment, you'd want to properly configure SSL certificates.

##   Author

Cameron Murphy - Swinburne University