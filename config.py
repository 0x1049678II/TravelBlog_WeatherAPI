"""
Configuration Module for my API Framework.

This module provides configuration settings for the app, including API keys,
base URLs, and application settings. It uses environment variables for sensitive
information and defines the itinerary locations.

Author: Cameron Murphy
Date: May 5th 2025
"""

import os
import re
from dotenv import load_dotenv

# Load the environment variables from .env file
load_dotenv()


class Config:
    """
    Configuration class for the API Framework.
    Contains all configuration settings for the Blog.
    """

    # API settings
    OPENWEATHERMAP_API_KEY = os.getenv('OPENWEATHERMAP_API_KEY', '')
    OPENWEATHERMAP_BASE_URL = 'https://api.openweathermap.org/data/2.5'

    # Application settings
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24).hex())

    # Cache settings
    CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'True').lower() == 'true'
    CACHE_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', '1800'))  # 30 minutes by default

    # API rate limiting
    RATE_LIMIT_CALLS = int(os.getenv('RATE_LIMIT_CALLS', '60'))  # Calls per minute
    RATE_LIMIT_PERIOD = int(os.getenv('RATE_LIMIT_PERIOD', '60'))  # Period in seconds

    # Itinerary - Locations with coordinates in England
    LOCATIONS = [
        {"name": "Cumbria", "lat": 54.4609, "lon": -3.0886},
        {"name": "Corfe Castle", "lat": 50.6395, "lon": -2.0566},
        {"name": "The Cotswolds", "lat": 51.8330, "lon": -1.8433},
        {"name": "Cambridge", "lat": 52.2053, "lon": 0.1218},
        {"name": "Bristol", "lat": 51.4545, "lon": -2.5879},
        {"name": "Oxford", "lat": 51.7520, "lon": -1.2577},
        {"name": "Norwich", "lat": 52.6309, "lon": 1.2974},
        {"name": "Stonehenge", "lat": 51.1789, "lon": -1.8262},
        {"name": "Watergate Bay", "lat": 50.4429, "lon": -5.0553},
        {"name": "Birmingham", "lat": 52.4862, "lon": -1.8904}
    ]

    @classmethod
    def validate_api_key(cls):
        """
        Validates that the OpenWeatherMap API key is properly formatted.

        Returns:
            bool: True if API key is valid, False otherwise
        """
        if not cls.OPENWEATHERMAP_API_KEY:
            return False

        # OpenWeatherMap API keys are 32 character hexadecimal strings
        pattern = re.compile(r'^[0-9a-f]{32}$')
        return bool(pattern.match(cls.OPENWEATHERMAP_API_KEY.lower()))

    @classmethod
    def get_location_by_name(cls, name):
        """
        Retrieves location data by name.

        Args:
            name (str): Location name to search for

        Returns:
            dict: Location data or None if not found
        """
        normalized_name = name.lower().replace('-', ' ')
        for location in cls.LOCATIONS:
            if location['name'].lower() == normalized_name:
                return location
        return None

    @classmethod
    def get_location_names(cls):
        """
        Returns a list of all location names in the itinerary.

        Returns:
            list: List of location names
        """
        return [location['name'] for location in cls.LOCATIONS]

    @classmethod
    def format_location_url(cls, location_name):
        """
        Formats a location name for use in URLs.

        Args:
            location_name (str): The location name to format

        Returns:
            str: URL-friendly location name
        """
        # Use regex to replace spaces and special characters
        return re.sub(r'[^a-z0-9]', '-', location_name.lower())