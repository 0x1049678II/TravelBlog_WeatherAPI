"""
The API Client module.

This module provides a client for interacting with the OpenWeatherMap API.
It includes decorators for rate limiting and caching, asynchronous API calls,
and error handling.

Author: Cameron Murphy
Date: May 6th 2025
"""

import asyncio
import functools
import json
import logging
import re
import ssl
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Callable, Optional, TypeVar, cast

import aiohttp
import requests
from requests.exceptions import RequestException

from config import Config
from models.weather import Weather, WeatherDataError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add a warning about SSL verification being disabled (needed for macOS)
logger.warning("SSL certificate verification is disabled for development. Not recommended for production!")

# Type variable for decorator return type preservation
T = TypeVar('T')


class APIError(Exception):
    """Base exception for API related errors."""
    pass


class RateLimitExceeded(APIError):
    """Exception raised when API rate limit is exceeded."""
    pass


class InvalidAPIKey(APIError):
    """Exception raised when API key is invalid."""
    pass


class LocationNotFound(APIError):
    """Exception raised when location is not found."""
    pass


class ConnectionError(APIError):
    """Exception raised when connection to API fails."""
    pass


class ResponseParsingError(APIError):
    """Exception raised when API response cannot be parsed."""
    pass


# Cache for storing API responses
api_cache: Dict[str, Dict[str, Any]] = {}


def rate_limit(calls: int = 60, period: int = 60) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to implement rate limiting for API calls.

    Args:
        calls: Maximum number of calls allowed in the period
        period: Time period in seconds

    Returns:
        Decorator function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Store timestamps of recent calls
        recent_calls = []

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            nonlocal recent_calls

            # Clean up old calls
            current_time = time.time()
            recent_calls = [t for t in recent_calls if current_time - t < period]

            # Check if rate limit exceeded
            if len(recent_calls) >= calls:
                remaining = period - (current_time - recent_calls[0])
                raise RateLimitExceeded(
                    f"Rate limit exceeded. Try again in {remaining:.1f} seconds."
                )

            # Add current call
            recent_calls.append(current_time)

            # Execute the function
            return func(*args, **kwargs)

        return wrapper

    return decorator


def cache_response(timeout: int = 1800) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to cache API responses.

    Args:
        timeout: Cache timeout in seconds (default: 30 minutes)

    Returns:
        Decorator function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Generate cache key based on function name and arguments
            key_parts = [func.__name__]

            # Add positional args to key
            for arg in args:
                key_parts.append(str(arg))

            # Add keyword args to key (sorted for consistency)
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")

            cache_key = ":".join(key_parts)

            # Clean invalid cache keys using regex
            cache_key = re.sub(r'[^a-zA-Z0-9_:=.-]', '_', cache_key)

            # Check if result in cache and not expired
            if cache_key in api_cache:
                entry = api_cache[cache_key]
                if datetime.now() < entry['expires']:
                    logger.info(f"Cache hit for {cache_key}")
                    return cast(T, entry['data'])

            # Call the function
            result = func(*args, **kwargs)

            # Store in cache
            api_cache[cache_key] = {
                'data': result,
                'expires': datetime.now() + timedelta(seconds=timeout)
            }

            return result

        return wrapper

    return decorator


class WeatherAPIClient:
    """
    Client for interacting with the OpenWeatherMap API.

    This class provides methods for retrieving weather data from the
    OpenWeatherMap API, with features for rate limiting, caching,
    and asynchronous requests.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the API client.

        Args:
            api_key: OpenWeatherMap API key (defaults to Config.OPENWEATHERMAP_API_KEY)
        """
        self.api_key = api_key or Config.OPENWEATHERMAP_API_KEY
        self.base_url = Config.OPENWEATHERMAP_BASE_URL

        # Validate API key
        if not self.api_key:
            raise InvalidAPIKey("API key is missing. Check your environment variables.")

        # Use regex to validate API key format
        if not re.match(r'^[0-9a-f]{32}$', self.api_key.lower()):
            logger.warning("API key format may be invalid. Check your API key.")

    @rate_limit(calls=Config.RATE_LIMIT_CALLS, period=Config.RATE_LIMIT_PERIOD)
    @cache_response(timeout=Config.CACHE_TIMEOUT)
    def get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Get current weather data for a location by coordinates.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dict[str, Any]: Weather data

        Raises:
            Various APIError subclasses on failure
        """
        endpoint = f"{self.base_url}/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key
        }

        try:
            # Disable SSL verification to fix macOS SSL issue
            response = requests.get(endpoint, params=params, timeout=10, verify=False)

            # Check for HTTP errors
            response.raise_for_status()

            # Parse JSON response
            data = response.json()

            # Check for API errors
            if 'cod' in data and data['cod'] != 200:
                error_msg = data.get('message', 'Unknown API error')

                # Handle specific error codes
                if data['cod'] == 401:
                    raise InvalidAPIKey(f"Invalid API key: {error_msg}")
                elif data['cod'] == 404:
                    raise LocationNotFound(f"Location not found: {error_msg}")
                elif data['cod'] == 429:
                    raise RateLimitExceeded(f"Rate limit exceeded: {error_msg}")
                else:
                    raise APIError(f"API error: {error_msg}")

            return data

        except RequestException as e:
            raise ConnectionError(f"Failed to connect to API: {str(e)}")
        except json.JSONDecodeError as e:
            raise ResponseParsingError(f"Failed to parse API response: {str(e)}")

    @rate_limit(calls=Config.RATE_LIMIT_CALLS, period=Config.RATE_LIMIT_PERIOD)
    @cache_response(timeout=Config.CACHE_TIMEOUT)
    def get_weather_by_location_name(self, location: str) -> Dict[str, Any]:
        """
        Get current weather data for a location by name.

        Args:
            location: Location name

        Returns:
            Dict[str, Any]: Weather data

        Raises:
            Various APIError subclasses on failure
        """
        endpoint = f"{self.base_url}/weather"
        params = {
            'q': location,
            'appid': self.api_key
        }

        try:
            # Disable SSL verification to fix macOS SSL issue
            response = requests.get(endpoint, params=params, timeout=10, verify=False)

            # Check for HTTP errors
            response.raise_for_status()

            # Parse JSON response
            data = response.json()

            # Check for API errors
            if 'cod' in data and data['cod'] != 200:
                error_msg = data.get('message', 'Unknown API error')

                # Handle specific error codes
                if data['cod'] == 401:
                    raise InvalidAPIKey(f"Invalid API key: {error_msg}")
                elif data['cod'] == 404:
                    raise LocationNotFound(f"Location not found: {error_msg}")
                elif data['cod'] == 429:
                    raise RateLimitExceeded(f"Rate limit exceeded: {error_msg}")
                else:
                    raise APIError(f"API error: {error_msg}")

            return data

        except RequestException as e:
            raise ConnectionError(f"Failed to connect to API: {str(e)}")
        except json.JSONDecodeError as e:
            raise ResponseParsingError(f"Failed to parse API response: {str(e)}")

    @rate_limit(calls=Config.RATE_LIMIT_CALLS, period=Config.RATE_LIMIT_PERIOD)
    @cache_response(timeout=Config.CACHE_TIMEOUT)
    def get_weather_forecast(self, lat: float, lon: float, days: int = 5) -> Dict[str, Any]:
        """
        Get weather forecast for a location.

        Args:
            lat: Latitude
            lon: Longitude
            days: Number of days for forecast (max 5)

        Returns:
            Dict[str, Any]: Forecast data

        Raises:
            Various APIError subclasses on failure
        """
        endpoint = f"{self.base_url}/forecast"
        params = {
            'lat': lat,
            'lon': lon,
            'cnt': min(days * 8, 40),  # 8 forecasts per day, max 40
            'appid': self.api_key
        }

        try:
            # Disable SSL verification to fix macOS SSL issue
            response = requests.get(endpoint, params=params, timeout=10, verify=False)

            # Check for HTTP errors
            response.raise_for_status()

            # Parse JSON response
            data = response.json()

            # Check for API errors
            if 'cod' in data and data['cod'] != '200':
                error_msg = data.get('message', 'Unknown API error')

                # Handle specific error codes
                if data['cod'] == '401':
                    raise InvalidAPIKey(f"Invalid API key: {error_msg}")
                elif data['cod'] == '404':
                    raise LocationNotFound(f"Location not found: {error_msg}")
                elif data['cod'] == '429':
                    raise RateLimitExceeded(f"Rate limit exceeded: {error_msg}")
                else:
                    raise APIError(f"API error: {error_msg}")

            return data

        except RequestException as e:
            raise ConnectionError(f"Failed to connect to API: {str(e)}")
        except json.JSONDecodeError as e:
            raise ResponseParsingError(f"Failed to parse API response: {str(e)}")

    async def get_all_locations_weather_async(self) -> Dict[str, Weather]:
        """
        Asynchronously retrieve weather data for all locations in the itinerary.

        Returns:
            Dict[str, Weather]: Dictionary of Weather objects indexed by location name

        Raises:
            Various APIError subclasses on failure
        """

        async def fetch_location_weather(session: aiohttp.ClientSession, location: Dict[str, Any]) -> Weather:
            """Helper function to fetch weather for a single location."""
            location_name = location['name']
            lat, lon = location['lat'], location['lon']

            url = f"{self.base_url}/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key
            }

            try:
                # Use cache if available
                cache_key = f"get_current_weather:{lat}:{lon}"
                if Config.CACHE_ENABLED and cache_key in api_cache:
                    entry = api_cache[cache_key]
                    if datetime.now() < entry['expires']:
                        logger.info(f"Cache hit for {location_name}")
                        return Weather(location_name, entry['data'])

                # Create SSL context that doesn't verify certificates (for macOS compatibility)
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

                # Make API request with SSL verification disabled
                async with session.get(url, params=params, ssl=ssl_context) as response:
                    if response.status != 200:
                        text = await response.text()
                        error_msg = f"API error for {location_name}: {response.status} - {text}"
                        logger.error(error_msg)
                        raise APIError(error_msg)

                    data = await response.json()

                    # Update cache
                    if Config.CACHE_ENABLED:
                        api_cache[cache_key] = {
                            'data': data,
                            'expires': datetime.now() + timedelta(seconds=Config.CACHE_TIMEOUT)
                        }

                    return Weather(location_name, data)

            except aiohttp.ClientError as e:
                logger.error(f"Connection error for {location_name}: {str(e)}")
                raise ConnectionError(f"Failed to connect to API for {location_name}: {str(e)}")
            except json.JSONDecodeError as e:
                logger.error(f"Parse error for {location_name}: {str(e)}")
                raise ResponseParsingError(f"Failed to parse API response for {location_name}: {str(e)}")
            except WeatherDataError as e:
                logger.error(f"Weather data error for {location_name}: {str(e)}")
                raise

        results = {}

        # Create aiohttp session
        async with aiohttp.ClientSession() as session:
            # Create tasks for each location
            tasks = [
                fetch_location_weather(session, location)
                for location in Config.LOCATIONS
            ]

            # Execute tasks concurrently
            for task in asyncio.as_completed(tasks):
                try:
                    weather = await task
                    results[weather.location] = weather
                except Exception as e:
                    logger.error(f"Error fetching weather: {str(e)}")
                    # Continue with other locations on error

        return results

    def get_all_locations_weather(self) -> Dict[str, Weather]:
        """
        Retrieve weather data for all locations in the itinerary.

        This is a synchronous wrapper around the async method.

        Returns:
            Dict[str, Weather]: Dictionary of Weather objects indexed by location name
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # Create new event loop if none exists
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.get_all_locations_weather_async())

    def get_weather_for_location(self, location_name: str) -> Weather:
        """
        Get weather for a specific location in the itinerary.

        Args:
            location_name: Name of the location

        Returns:
            Weather: Weather object for the location

        Raises:
            LocationNotFound: If location is not found in the itinerary
            Various other APIError subclasses on failure
        """
        location = Config.get_location_by_name(location_name)
        if not location:
            raise LocationNotFound(f"Location '{location_name}' not found in itinerary")

        data = self.get_current_weather(location['lat'], location['lon'])
        return Weather(location_name, data)
