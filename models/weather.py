"""
Weather Data Model for my API Framework.

This module defines the Weather class that represents weather data for a location.
It handles data validation, transformation, and provides methods for accessing and
displaying weather information in different formats.

Author: Cameron Murphy
Date: May 5th 2025
"""

import datetime
import re
from dataclasses import dataclass
from typing import Dict, Any


class WeatherDataError(Exception):
    """Exception raised for errors in the weather data."""
    pass


@dataclass
class WeatherCondition:
    """Class representing a weather condition."""
    id: int
    main: str
    description: str
    icon: str

    @property
    def icon_url(self) -> str:
        """Returns the URL for the weather icon."""
        return f"https://openweathermap.org/img/wn/{self.icon}@2x.png"

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'WeatherCondition':
        """
        Creates a WeatherCondition instance from API data.

        Args:
            data: Dictionary containing weather condition data from the API

        Returns:
            WeatherCondition: An instance with the parsed data

        Raises:
            WeatherDataError: If required fields are missing
        """
        try:
            return cls(
                id=data['id'],
                main=data['main'],
                description=data['description'].capitalize(),
                icon=data['icon']
            )
        except KeyError as e:
            raise WeatherDataError(f"Missing required field in weather condition data: {e}")


class Weather:
    """
    Class representing weather data for a location.

    Attributes:
        location (str): Name of the location
        temp (float): Current temperature in Celsius
        feels_like (float): "Feels like" temperature in Celsius
        temp_min (float): Minimum temperature in Celsius
        temp_max (float): Maximum temperature in Celsius
        pressure (int): Atmospheric pressure in hPa
        humidity (int): Humidity percentage
        wind_speed (float): Wind speed in meters/second
        wind_deg (int): Wind direction in degrees
        conditions (List[WeatherCondition]): List of weather conditions
        clouds (int): Cloudiness percentage
        timestamp (datetime): Time of data calculation, UTC
        timezone (int): Timezone offset in seconds from UTC
        rain_1h (Optional[float]): Rain volume for last hour in mm
        rain_3h (Optional[float]): Rain volume for last 3 hours in mm
        snow_1h (Optional[float]): Snow volume for last hour in mm
        snow_3h (Optional[float]): Snow volume for last 3 hours in mm
        sunrise (datetime): Sunrise time, UTC
        sunset (datetime): Sunset time, UTC
        visibility (Optional[int]): Visibility in meters
    """

    def __init__(self, location: str, data: Dict[str, Any]):
        """
        Initialize a Weather instance from API data.

        Args:
            location: Name of the location
            data: Weather data from the API

        Raises:
            WeatherDataError: If data validation fails
        """
        self.location = location

        # Validate and process the data
        self._validate_data(data)

        # Main weather attributes
        main = data['main']
        self.temp = self._kelvin_to_celsius(main['temp'])
        self.feels_like = self._kelvin_to_celsius(main['feels_like'])
        self.temp_min = self._kelvin_to_celsius(main['temp_min'])
        self.temp_max = self._kelvin_to_celsius(main['temp_max'])
        self.pressure = main['pressure']
        self.humidity = main['humidity']

        # Wind
        wind = data['wind']
        self.wind_speed = wind['speed']
        self.wind_deg = wind.get('deg', 0)

        # Weather conditions
        self.conditions = [WeatherCondition.from_api_data(cond) for cond in data['weather']]

        # Clouds
        self.clouds = data['clouds']['all']

        # Time-related data
        self.timestamp = datetime.datetime.fromtimestamp(data['dt'], datetime.timezone.utc)
        self.timezone = data.get('timezone', 0)

        # Optional data
        self.rain_1h = data.get('rain', {}).get('1h')
        self.rain_3h = data.get('rain', {}).get('3h')
        self.snow_1h = data.get('snow', {}).get('1h')
        self.snow_3h = data.get('snow', {}).get('3h')

        # Sun data
        sys = data.get('sys', {})
        self.sunrise = datetime.datetime.fromtimestamp(sys.get('sunrise', 0), datetime.timezone.utc)
        self.sunset = datetime.datetime.fromtimestamp(sys.get('sunset', 0), datetime.timezone.utc)

        # Visibility
        self.visibility = data.get('visibility')

    def _validate_data(self, data: Dict[str, Any]) -> None:
        """
        Validates that the API data contains all required fields.

        Args:
            data: Weather data from the API

        Raises:
            WeatherDataError: If required fields are missing
        """
        required_fields = ['main', 'wind', 'weather', 'clouds', 'dt']
        for field in required_fields:
            if field not in data:
                raise WeatherDataError(f"Missing required field: {field}")

        # Validate main fields
        required_main_fields = ['temp', 'feels_like', 'temp_min', 'temp_max', 'pressure', 'humidity']
        for field in required_main_fields:
            if field not in data['main']:
                raise WeatherDataError(f"Missing required field in main data: {field}")

    @staticmethod
    def _kelvin_to_celsius(kelvin: float) -> float:
        """
        Converts temperature from Kelvin to Celsius.

        Args:
            kelvin: Temperature in Kelvin

        Returns:
            float: Temperature in Celsius, rounded to 1 decimal place
        """
        return round(kelvin - 273.15, 1)

    @property
    def main_condition(self) -> WeatherCondition:
        """Returns the primary weather condition."""
        return self.conditions[0] if self.conditions else None

    @property
    def local_time(self) -> datetime.datetime:
        """Returns the local time at the location."""
        return self.timestamp.replace(tzinfo=datetime.timezone.utc).astimezone(
            datetime.timezone(datetime.timedelta(seconds=self.timezone))
        )

    @property
    def local_sunrise(self) -> datetime.datetime:
        """Returns the local sunrise time."""
        return self.sunrise.replace(tzinfo=datetime.timezone.utc).astimezone(
            datetime.timezone(datetime.timedelta(seconds=self.timezone))
        )

    @property
    def local_sunset(self) -> datetime.datetime:
        """Returns the local sunset time."""
        return self.sunset.replace(tzinfo=datetime.timezone.utc).astimezone(
            datetime.timezone(datetime.timedelta(seconds=self.timezone))
        )

    @property
    def is_daytime(self) -> bool:
        """Returns True if it's currently daytime at the location."""
        now = self.local_time
        return self.local_sunrise <= now <= self.local_sunset

    @property
    def wind_direction(self) -> str:
        """
        Returns the cardinal direction of the wind.
        Uses regex pattern matching to determine the direction.
        """
        # Define direction boundaries using regex patterns
        directions = [
            (r'^(3[3-9]|[01]?[0-9]?[0-9])$', 'N'),  # 339-360, 0-22.5
            (r'^(2[2-6]|2[0-2])$', 'NE'),  # 22.5-67.5
            (r'^(6[8-9]|[7-9][0-9]|1[0-1][0-9])$', 'E'),  # 67.5-112.5
            (r'^(1[1-3][0-9]|1[5-6][0-9])$', 'SE'),  # 112.5-157.5
            (r'^(1[5-7][0-9]|1[8-9][0-9]|20[0-2])$', 'S'),  # 157.5-202.5
            (r'^(20[2-9]|2[1-4][0-9])$', 'SW'),  # 202.5-247.5
            (r'^(2[4-7][0-9]|2[8-9][0-9]|30[0-2])$', 'W'),  # 247.5-292.5
            (r'^(29[2-9]|3[0-3][0-9])$', 'NW')  # 292.5-339
        ]

        # Convert wind_deg to 0-360 range
        deg = int(self.wind_deg) % 360

        # Match against patterns
        for pattern, direction in directions:
            if re.match(pattern, str(deg)):
                return direction

        return 'N'  # Default fallback

    def get_summary(self) -> Dict[str, Any]:
        """
        Returns a summary of the weather data.

        Returns:
            Dict[str, Any]: Summary of weather data
        """
        return {
            'location': self.location,
            'temp': self.temp,
            'condition': self.main_condition.main if self.main_condition else 'Unknown',
            'description': self.main_condition.description if self.main_condition else 'Unknown',
            'icon': self.main_condition.icon_url if self.main_condition else '',
            'humidity': self.humidity,
            'wind_speed': self.wind_speed,
            'wind_direction': self.wind_direction,
            'time': self.local_time.strftime('%H:%M %d/%m/%Y'),
            'is_daytime': self.is_daytime
        }

    def format_for_blog(self) -> str:
        """
        Returns a formatted text description for blog posts.

        Returns:
            str: Formatted weather description for blog posts
        """
        time_str = self.local_time.strftime('%A, %B %d at %I:%M %p')

        description = f"Weather in {self.location} on {time_str}:\n"
        description += f"Temperature: {self.temp}°C (feels like {self.feels_like}°C)\n"
        description += f"Conditions: {self.main_condition.description if self.main_condition else 'Unknown'}\n"
        description += f"Humidity: {self.humidity}%\n"
        description += f"Wind: {self.wind_speed} m/s from the {self.wind_direction}\n"

        if self.rain_1h:
            description += f"Rain (last hour): {self.rain_1h} mm\n"

        description += f"Sunrise: {self.local_sunrise.strftime('%I:%M %p')}\n"
        description += f"Sunset: {self.local_sunset.strftime('%I:%M %p')}\n"

        return description

    @classmethod
    def from_api_response(cls, location: str, response: Dict[str, Any]) -> 'Weather':
        """
        Creates a Weather instance from an API response.

        Args:
            location: Name of the location
            response: Complete API response

        Returns:
            Weather: An instance with the parsed data

        Raises:
            WeatherDataError: If the response is invalid
        """
        if not isinstance(response, dict):
            raise WeatherDataError("Invalid API response format")

        # Check for API error
        if 'cod' in response and response['cod'] != 200:
            error_msg = response.get('message', 'Unknown error')
            raise WeatherDataError(f"API error: {error_msg}")

        return cls(location, response)