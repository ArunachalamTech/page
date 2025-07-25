# Copyright 2021 To 2024-present, Author: MrAKTech

import logging
from aiohttp import web
from .stream_routes import routes
from MrAKTech.config import Server

# Try to import performance packages
try:
    import uvloop
    UVLOOP_AVAILABLE = True
except ImportError:
    UVLOOP_AVAILABLE = False

try:
    import aiodns
    AIODNS_AVAILABLE = True
except ImportError:
    AIODNS_AVAILABLE = False

logger = logging.getLogger("server")

def web_server():
    """
    Optimized web server configuration for high-performance streaming
    """
    logger.info("Initializing high-performance web server...")
    
    # Enhanced web application with optimized settings
    web_app = web.Application(
        client_max_size=50 * 1024 * 1024,  # 50MB max request size
    )
    
    # Add middleware for performance optimization
    web_app.middlewares.append(performance_middleware)
    web_app.add_routes(routes)
    
    logger.info("Added routes and performance middleware")
    return web_app


@web.middleware
async def performance_middleware(request, handler):
    """
    Performance optimization middleware
    """
    # Add performance headers
    response = await handler(request)
    
    # Add performance and security headers
    response.headers.update({
        'X-Frame-Options': 'DENY',
        'X-Content-Type-Options': 'nosniff',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Server': 'MrAK-HighSpeed/2.0',
    })
    
    return response
