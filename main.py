"""
Main entry point for my API Framework.

This script runs the Flask application and can be executed directly.
It sets up logging and handles command-line arguments.

Author: Cameron Murphy
Date: May 4th 2025
"""

import os
import argparse
import logging
from app import app

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='TravelBlog_WeatherAPI Server')
    parser.add_argument(
        '--port',
        type=int,
        default=int(os.environ.get('PORT', 5000)),
        help='Port to run the server on (default: 5000 or PORT env var)'
    )
    parser.add_argument(
        '--host',
        type=str,
        default=os.environ.get('HOST', '0.0.0.0'),
        help='Host to run the server on (default: 0.0.0.0 or HOST env var)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        default=os.environ.get('DEBUG', 'False').lower() == 'true',
        help='Run in debug mode (default: False or DEBUG env var)'
    )

    args = parser.parse_args()

    # Log startup information
    logger.info(f"Starting TravelBlog_WeatherAPI on {args.host}:{args.port}")
    logger.info(f"Debug mode: {args.debug}")

    try:
        # Run the Flask application
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug
        )
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        raise