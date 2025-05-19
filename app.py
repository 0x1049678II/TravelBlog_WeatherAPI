"""
Main Flask Application for the Blog.

This module defines the Flask app that serves as the web interface
for the weather API integration. It includes route handlers, error handling,
and template rendering.

Author: Cameron Murphy
Date: May 4th 2025
"""

import os
import re
import logging
import datetime
from typing import Tuple

from flask import Flask, render_template, request, jsonify, redirect, url_for, abort
from werkzeug.exceptions import HTTPException

from config import Config
from models.weather import WeatherDataError
from services.api_client import (
    WeatherAPIClient, InvalidAPIKey,
    LocationNotFound, ConnectionError, ResponseParsingError, RateLimitExceeded
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['DEBUG'] = Config.DEBUG

# Initialize API client
try:
    api_client = WeatherAPIClient()
except InvalidAPIKey as e:
    logger.error(f"API Key Error: {str(e)}")
    api_client = None


@app.context_processor
def inject_now():
    """
    Add the current datetime to all templates.
    This allows using {{ now.year }} in templates.
    """
    return {'now': datetime.datetime.now()}


@app.before_request
def check_api_key():
    """
    Middleware to check for a valid API key before processing requests.
    Redirects to error page if API key is invalid.
    """
    if not api_client:
        # Skip check for error routes
        if request.path.startswith('/error') or request.path.startswith('/static'):
            return None

        return redirect(url_for('error', code=500, message="API key is invalid or missing"))
    return None


@app.errorhandler(Exception)
def handle_exception(e: Exception) -> Tuple[str, int]:
    """
    Global exception handler for all routes.

    Args:
        e: The exception that was raised

    Returns:
        Tuple[str, int]: Response and status code
    """
    logger.error(f"Exception: {str(e)}", exc_info=True)

    # Handle specific API errors
    if isinstance(e, InvalidAPIKey):
        return render_template('error.html',
                               error="API Key Error",
                               message="The API key is invalid or missing."), 500
    elif isinstance(e, LocationNotFound):
        return render_template('error.html',
                               error="Location Not Found",
                               message=str(e)), 404
    elif isinstance(e, ConnectionError):
        return render_template('error.html',
                               error="Connection Error",
                               message="Could not connect to the weather API. Please try again later."), 503
    elif isinstance(e, ResponseParsingError):
        return render_template('error.html',
                               error="Response Error",
                               message="Could not parse the API response."), 500
    elif isinstance(e, RateLimitExceeded):
        return render_template('error.html',
                               error="Rate Limit Exceeded",
                               message="Too many requests. Please try again later."), 429
    elif isinstance(e, WeatherDataError):
        return render_template('error.html',
                               error="Weather Data Error",
                               message=str(e)), 500
    elif isinstance(e, HTTPException):
        return render_template('error.html',
                               error=f"{e.code} - {e.name}",
                               message=e.description), e.code

    # Generic error handler
    return render_template('error.html',
                           error="Server Error",
                           message="An unexpected error occurred."), 500


@app.route('/')
def index():
    """
    Render the index page with a list of locations.

    Returns:
        str: Rendered HTML template
    """
    locations = Config.get_location_names()
    return render_template('index.html', locations=locations)


@app.route('/weather/<location_name>')
def weather(location_name: str):
    """
    Display weather for a specific location.

    Args:
        location_name: Name of the location

    Returns:
        str: Rendered HTML template
    """
    # Normalize location name using regex
    normalized_name = re.sub(r'-', ' ', location_name).title()

    try:
        # Get weather data
        weather_data = api_client.get_weather_for_location(normalized_name)

        # Get location data for map
        location = Config.get_location_by_name(normalized_name)

        return render_template(
            'weather.html',
            weather=weather_data,
            location=location,
            api_key=Config.OPENWEATHERMAP_API_KEY
        )
    except LocationNotFound:
        abort(404, f"Location '{normalized_name}' not found")
    except Exception as e:
        logger.error(f"Error in weather route: {str(e)}", exc_info=True)
        raise


@app.route('/api/weather/<location_name>')
def api_weather(location_name: str):
    """
    API endpoint to get weather data for a specific location.

    Args:
        location_name: Name of the location

    Returns:
        Dict[str, Any]: JSON response with weather data
    """
    # Normalize location name using regex
    normalized_name = re.sub(r'-', ' ', location_name).title()

    try:
        # Get weather data
        weather_data = api_client.get_weather_for_location(normalized_name)

        # Return JSON
        return jsonify({
            'success': True,
            'data': weather_data.get_summary()
        })
    except LocationNotFound:
        return jsonify({
            'success': False,
            'error': 'Location not found',
            'message': f"Location '{normalized_name}' not found"
        }), 404
    except Exception as e:
        logger.error(f"Error in API weather route: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': str(e)
        }), 500


@app.route('/api/weather/all')
def api_all_weather():
    """
    API endpoint to get weather data for all locations.

    Returns:
        Dict[str, Any]: JSON response with weather data for all locations
    """
    try:
        # Get weather data for all locations
        all_weather = api_client.get_all_locations_weather()

        # Prepare response
        data = {
            location: weather.get_summary()
            for location, weather in all_weather.items()
        }

        # Return JSON
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        logger.error(f"Error in API all weather route: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': str(e)
        }), 500


@app.route('/dashboard')
def dashboard():
    """
    Display a dashboard with weather for all locations.

    Returns:
        str: Rendered HTML template
    """
    try:
        # Get weather data for all locations
        all_weather = api_client.get_all_locations_weather()

        # Get all locations data for map
        locations = Config.LOCATIONS

        return render_template(
            'dashboard.html',
            weather_data=all_weather,
            locations=locations,
            api_key=Config.OPENWEATHERMAP_API_KEY
        )
    except Exception as e:
        logger.error(f"Error in dashboard route: {str(e)}", exc_info=True)
        raise


@app.route('/error')
def error():
    """
    Display an error page.

    Returns:
        str: Rendered HTML template
    """
    code = request.args.get('code', 500)
    message = request.args.get('message', 'An unexpected error occurred')

    return render_template('error.html', error=f"Error {code}", message=message), int(code)


@app.route('/about')
def about():
    """
    Display information about the application.

    Returns:
        str: Rendered HTML template
    """
    return render_template('about.html')

# Custom template filters
@app.template_filter('wind_direction_arrow')
def wind_direction_arrow(degrees: float) -> str:
    """
    Convert wind direction degrees to an arrow character.

    Args:
        degrees: Wind direction in degrees

    Returns:
        str: Arrow character representing the direction
    """
    # Using regex to match degree ranges to arrows
    arrows = [
        (r'^(3[3-9]|[01]?[0-9]?[0-9])$', '↓'),     # North (339-360, 0-22.5)
        (r'^(2[2-6]|2[0-2])$', '↙'),               # Northeast (22.5-67.5)
        (r'^(6[8-9]|[7-9][0-9]|1[0-1][0-9])$', '←'), # East (67.5-112.5)
        (r'^(1[1-3][0-9]|1[5-6][0-9])$', '↖'),     # Southeast (112.5-157.5)
        (r'^(1[5-7][0-9]|1[8-9][0-9]|20[0-2])$', '↑'), # South (157.5-202.5)
        (r'^(20[2-9]|2[1-4][0-9])$', '↗'),         # Southwest (202.5-247.5)
        (r'^(2[4-7][0-9]|2[8-9][0-9]|30[0-2])$', '→'), # West (247.5-292.5)
        (r'^(29[2-9]|3[0-3][0-9])$', '↘')          # Northwest (292.5-339)
    ]

    # Convert degrees to 0-360 range
    deg = int(degrees) % 360

    # Match against patterns
    for pattern, arrow in arrows:
        if re.match(pattern, str(deg)):
            return arrow

    return '↓'  # Default fallback


if __name__ == '__main__':
    # Run the Flask application
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)