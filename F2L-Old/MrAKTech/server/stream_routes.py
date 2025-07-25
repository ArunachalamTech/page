# Copyright 2021 To 2024-present, Author: MrAKTech

import re
import time
import random
import datetime
import math
import logging
import mimetypes
import secrets
from aiohttp import web
from aiohttp.http_exceptions import BadStatusLine

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from MrAKTech import StreamBot, multi_clients, work_loads
from MrAKTech.server.exceptions import FIleNotFound, InvalidHash
from MrAKTech.tools.custom_dl import ByteStreamer, chunk_size, offset_fix
from MrAKTech.tools.render_template import render_page
from MrAKTech.tools.utils_bot import temp, readable_time
from MrAKTech.tools.file_properties import get_file_ids, get_namex
from MrAKTech.tools.human_readable import humanbytes
from MrAKTech.tools.txt import tamilxd
from MrAKTech.config import Telegram, Server, Domain

logger = logging.getLogger("routes")

routes = web.RouteTableDef()


@routes.get("/", allow_head=True)
async def root_route_handler(_):
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-49K41Q9T85"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-49K41Q9T85');
</script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MrAK Tech - Premium Streaming Platform</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Poppins:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
    <style>
        :root {
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --success-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            --warning-gradient: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
            --danger-gradient: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
            --dark-gradient: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            --light-gradient: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
            --dark-theme-gradient: linear-gradient(135deg, #2d3436 0%, #636e72 100%);
            --card-shadow: 0 25px 50px rgba(0,0,0,0.15);
            --hover-shadow: 0 35px 70px rgba(0,0,0,0.25);
            --border-radius: 25px;
            --transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', 'Poppins', sans-serif;
            background: var(--primary-gradient);
            color: white;
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
            transition: var(--transition);
        }

        body.dark-theme {
            background: var(--dark-theme-gradient);
            color: #ddd;
        }

        body.light-theme {
            background: var(--light-gradient);
            color: #2d3436;
        }

        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 25% 25%, rgba(255,255,255,0.1) 0%, transparent 70%),
                radial-gradient(circle at 75% 75%, rgba(255,255,255,0.1) 0%, transparent 70%);
            pointer-events: none;
            z-index: -1;
        }

        .header {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            text-align: center;
            padding: 30px 0;
            position: relative;
        }

        .theme-toggle-container {
            position: absolute;
            top: 50%;
            right: 30px;
            transform: translateY(-50%);
        }

        .theme-toggle-btn {
            cursor: pointer;
            border-radius: 50px;
            padding: 10px 20px;
            font-weight: 600;
            transition: var(--transition);
            border: 2px solid rgba(255,255,255,0.3);
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            color: white;
            text-decoration: none;
            font-size: 14px;
        }

        .theme-toggle-btn:hover {
            transform: scale(1.05);
            background: rgba(255,255,255,0.2);
            color: white;
        }

        .light-theme .theme-toggle-btn {
            border: 2px solid rgba(45, 52, 54, 0.3);
            background: rgba(45, 52, 54, 0.1);
            color: #2d3436;
        }

        .light-theme .theme-toggle-btn:hover {
            background: rgba(45, 52, 54, 0.2);
            color: #2d3436;
        }

        .header h1 {
            font-family: 'Poppins', sans-serif;
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(45deg, #fff, #f0f0f0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 4px 15px rgba(0,0,0,0.3);
            animation: glow 2s ease-in-out infinite alternate;
            transition: var(--transition);
        }

        .light-theme .header h1 {
            background: linear-gradient(45deg, #2d3436, #636e72);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 4px 15px rgba(255,255,255,0.3);
        }

        .dark-theme .header h1 {
            background: linear-gradient(45deg, #fff, #f0f0f0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }

        @keyframes glow {
            from { filter: drop-shadow(0 0 20px rgba(255,255,255,0.3)); }
            to { filter: drop-shadow(0 0 30px rgba(255,255,255,0.5)); }
        }

        .content {
            padding: 60px 20px;
            text-align: center;
            max-width: 1200px;
            margin: 0 auto;
        }

        .hero-section {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border-radius: var(--border-radius);
            padding: 60px 40px;
            margin: 40px 0;
            box-shadow: var(--card-shadow);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: var(--transition);
        }

        body.dark-theme .hero-section {
            background: rgba(45, 52, 54, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        body.light-theme .hero-section {
            background: rgba(255, 255, 255, 0.25);
            border: 1px solid rgba(116, 185, 255, 0.3);
        }

        .hero-section:hover {
            transform: translateY(-10px);
            box-shadow: var(--hover-shadow);
        }

        .gif-container {
            margin: 40px 0;
            border-radius: var(--border-radius);
            overflow: hidden;
            box-shadow: var(--card-shadow);
            transition: var(--transition);
        }

        .gif-container:hover {
            transform: scale(1.05);
            box-shadow: var(--hover-shadow);
        }

        .image {
            border-radius: var(--border-radius);
            max-width: 100%;
            width: 100%;
            max-width: 500px;
            height: auto;
        }

        .welcome-text {
            font-size: 1.5rem;
            font-weight: 600;
            margin: 30px 0;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }

        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin: 50px 0;
        }

        .feature-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border-radius: var(--border-radius);
            padding: 40px 30px;
            text-align: center;
            box-shadow: var(--card-shadow);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: var(--transition);
        }

        body.dark-theme .feature-card {
            background: rgba(45, 52, 54, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        body.light-theme .feature-card {
            background: rgba(255, 255, 255, 0.3);
            border: 1px solid rgba(116, 185, 255, 0.3);
        }

        .feature-card:hover {
            transform: translateY(-10px);
            box-shadow: var(--hover-shadow);
            background: rgba(255, 255, 255, 0.15);
        }

        .feature-icon {
            font-size: 3rem;
            margin-bottom: 20px;
            color: #4facfe;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }

        .feature-title {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 15px;
        }

        .feature-description {
            font-size: 1rem;
            opacity: 0.9;
            line-height: 1.6;
        }

        .cta-button {
            background: var(--success-gradient);
            color: white;
            padding: 18px 40px;
            border: none;
            border-radius: 50px;
            font-size: 1.2rem;
            font-weight: 700;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 12px;
            cursor: pointer;
            transition: var(--transition);
            box-shadow: 0 15px 35px rgba(79, 172, 254, 0.3);
            text-transform: uppercase;
            letter-spacing: 1px;
            position: relative;
            overflow: hidden;
        }

        .cta-button:hover {
            transform: translateY(-5px);
            box-shadow: 0 25px 50px rgba(79, 172, 254, 0.4);
            color: white;
            text-decoration: none;
        }

        .cta-button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }

        .cta-button:hover::before {
            left: 100%;
        }

        .footer {
            background: rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            padding: 30px 0;
            text-align: center;
            margin-top: 60px;
            transition: var(--transition);
        }

        .light-theme .footer {
            background: rgba(255, 255, 255, 0.2);
            border-top: 1px solid rgba(45, 52, 54, 0.1);
        }

        .footer p {
            font-size: 1rem;
            opacity: 0.9;
            margin: 0;
            color: inherit;
        }

        .stats-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 30px;
            margin: 50px 0;
        }

        .stat-item {
            text-align: center;
            padding: 30px 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: var(--border-radius);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: var(--transition);
        }

        body.dark-theme .stat-item {
            background: rgba(45, 52, 54, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        body.light-theme .stat-item {
            background: rgba(255, 255, 255, 0.25);
            border: 1px solid rgba(116, 185, 255, 0.3);
        }

        .stat-item:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.15);
        }

        .stat-number {
            font-size: 3rem;
            font-weight: 800;
            color: #4facfe;
            margin-bottom: 10px;
        }

        .stat-label {
            font-size: 1.1rem;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        @media (max-width: 768px) {
            .header h1 {
                font-size: 2rem;
            }
            
            .hero-section {
                padding: 40px 20px;
                margin: 20px 0;
            }
            
            .welcome-text {
                font-size: 1.2rem;
            }
            
            .cta-button {
                padding: 15px 30px;
                font-size: 1rem;
            }
            
            .feature-grid {
                grid-template-columns: 1fr;
                gap: 20px;
            }
        }

        .floating-shapes {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: -1;
        }

        .shape {
            position: absolute;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 50%;
            animation: float 6s ease-in-out infinite;
        }

        .shape:nth-child(1) {
            width: 80px;
            height: 80px;
            top: 20%;
            left: 10%;
            animation-delay: 0s;
        }

        .shape:nth-child(2) {
            width: 120px;
            height: 120px;
            top: 60%;
            right: 10%;
            animation-delay: 2s;
        }

        .shape:nth-child(3) {
            width: 100px;
            height: 100px;
            bottom: 20%;
            left: 20%;
            animation-delay: 4s;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
        }
    </style>
</head>
<body>
    <div class="floating-shapes">
        <div class="shape"></div>
        <div class="shape"></div>
        <div class="shape"></div>
    </div>

    <div class="header">
        <h1>𝙼𝚁𝗔𝗞 𝐁𝐎𝐓𝐒</h1>
        <div class="theme-toggle-container">
            <button id="theme-toggle-btn" class="theme-toggle-btn">
                <i class="fa-solid fa-sun"></i> Light Theme
            </button>
        </div>
    </div>

    <div class="content">
        <div class="hero-section">
            <div class="gif-container">
                <img src="https://i.giphy.com/media/3o7abAHdYvZdBNnGZq/giphy.webp" class="image" alt="Streaming Animation">
            </div>
            <h2 class="welcome-text">🎬 Welcome to Premium Streaming Experience! 🚀</h2>
            <p style="font-size: 1.2rem; margin: 20px 0; opacity: 0.9;">
                Stream, Download, and Enjoy High-Quality Content with Advanced Technology
            </p>
            <a href="https://telegram.me/MrAK_BOTS" class="cta-button">
                <i class="fab fa-telegram"></i>
                Join Updates Channel
            </a>
        </div>

        <div class="feature-grid">
            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-play-circle"></i>
                </div>
                <h3 class="feature-title">HD Streaming</h3>
                <p class="feature-description">
                    Experience crystal-clear streaming with our advanced video player technology and multiple quality options.
                </p>
            </div>

            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-download"></i>
                </div>
                <h3 class="feature-title">Fast Downloads</h3>
                <p class="feature-description">
                    Lightning-fast download speeds with secure direct links and resume support for interrupted downloads.
                </p>
            </div>

            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-mobile-alt"></i>
                </div>
                <h3 class="feature-title">Mobile Friendly</h3>
                <p class="feature-description">
                    Optimized for all devices with responsive design that works perfectly on phones, tablets, and desktops.
                </p>
            </div>

            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-shield-alt"></i>
                </div>
                <h3 class="feature-title">Secure & Safe</h3>
                <p class="feature-description">
                    Your privacy matters. All content is served through secure connections with no malicious ads or trackers.
                </p>
            </div>

            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-rocket"></i>
                </div>
                <h3 class="feature-title">High Performance</h3>
                <p class="feature-description">
                    Powered by cutting-edge servers and CDN technology for minimal buffering and maximum speed.
                </p>
            </div>

            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-users"></i>
                </div>
                <h3 class="feature-title">24/7 Support</h3>
                <p class="feature-description">
                    Our dedicated support team is always ready to help you with any questions or technical issues.
                </p>
            </div>
        </div>

        <div class="stats-section">
            <div class="stat-item">
                <div class="stat-number">1M+</div>
                <div class="stat-label">Happy Users</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">99.9%</div>
                <div class="stat-label">Uptime</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">10TB+</div>
                <div class="stat-label">Content Served</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">50+</div>
                <div class="stat-label">Countries</div>
            </div>
        </div>
    </div>

    <div class="footer">
        <p>© 2024 𝙼𝚁𝗔𝗞 𝐁𝐎𝐓𝐒. All rights reserved. | Made with ❤️ in India</p>
    </div>

    <script>
        // Add smooth scrolling and interactive effects
        document.addEventListener('DOMContentLoaded', function() {
            // Theme toggle functionality
            const themeToggleBtn = document.getElementById('theme-toggle-btn');
            const currentTheme = localStorage.getItem('home-theme') || 'default';

            const applyTheme = (theme) => {
                // Remove all theme classes first
                document.body.classList.remove('light-theme', 'dark-theme');
                
                if (theme === 'light') {
                    document.body.classList.add('light-theme');
                    themeToggleBtn.innerHTML = '<i class="fa-solid fa-moon"></i> Dark Theme';
                } else if (theme === 'dark') {
                    document.body.classList.add('dark-theme');
                    themeToggleBtn.innerHTML = '<i class="fa-solid fa-sun"></i> Light Theme';
                } else {
                    // Default theme
                    themeToggleBtn.innerHTML = '<i class="fa-solid fa-sun"></i> Light Theme';
                }
                localStorage.setItem('home-theme', theme);
            };

            themeToggleBtn.addEventListener('click', () => {
                let newTheme;
                if (document.body.classList.contains('dark-theme')) {
                    newTheme = 'light';
                } else if (document.body.classList.contains('light-theme')) {
                    newTheme = 'dark';
                } else {
                    newTheme = 'light';
                }
                applyTheme(newTheme);
            });

            // Apply the saved theme on page load
            applyTheme(currentTheme);

            // Animate feature cards on scroll
            const observerOptions = {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            };

            const observer = new IntersectionObserver(function(entries) {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }
                });
            }, observerOptions);

            // Observe all feature cards
            document.querySelectorAll('.feature-card, .stat-item').forEach(card => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(30px)';
                card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                observer.observe(card);
            });

            // Add hover effect to CTA button
            const ctaButton = document.querySelector('.cta-button');
            ctaButton.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-5px) scale(1.05)';
            });
            ctaButton.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(-5px) scale(1)';
            });
        });
    </script>
</body>
</html>
"""
    return web.Response(text=html_content, content_type="text/html")


# @routes.get(r"/{path:\S+}")
# async def undefined_url_handler(request):
#     return web.HTTPFound("/error")


@routes.get("/error")
async def error_handler(request):
    html_content = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Error Page</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
  </head>
  <body>
    <div class="container">
      <h1>Error Page</h1>
      <p>Sorry, the requested page could not be found.</p>
      <p>Please check the URL or try again later.</p>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz" crossorigin="anonymous"></script>
  </body>
</html>
    """
    return web.Response(text=html_content, content_type="text/html")


@routes.post("/api/report")
async def api_handler(request):
    try:
        data = await request.json()
        logging.info(f"Received report: {data}")
        india_time = datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        )
        file_data = await get_file_ids(
            StreamBot, int(Telegram.FLOG_CHANNEL), int(data.get("file_id"))
        )
        await StreamBot.send_message(
            chat_id=Telegram.REPORT_GROUP,
            text=tamilxd.REPORT_TXT.format(
                date=india_time.strftime("%d-%B-%Y"),
                time=india_time.strftime("%I:%M:%S %p"),
                file_name=file_data.file_name,
                file_size=humanbytes(file_data.file_size),
                mime_type=file_data.mime_type,
                file_unique_id=file_data.unique_id,
                file_url=f"{Server.URL}watch/{data.get('file_id')}?hash={file_data.unique_id[:6]}",
                post_url=f"https://t.me/{str(Telegram.FLOG_CHANNEL).replace('-100','c/')}/{data.get('file_id')}",
                report=data.get("report"),
                report_msg=data.get("reportMsg"),
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Delete 🤷‍♂️", callback_data=f"delete_{data.get('file_id')}"
                        ),
                        InlineKeyboardButton("verify ☑️", callback_data="verify"),
                    ],
                    [InlineKeyboardButton("Close", callback_data="close")],
                ]
            ),
            disable_web_page_preview=True,
        )
        return web.json_response(
            {"status": "success", "message": "Data received and processed successfully"}
        )
    except Exception as e:
        logging.error(f"Error processing API request: {str(e)}")
        return web.json_response(
            {"status": "error", "message": "Failed to process the request"}
        )


@routes.post("/api/file")
async def api_handlerx(request):
    try:
        id = await request.json()
        file_data = await get_file_ids(
            StreamBot, int(Telegram.FLOG_CHANNEL), int(id.get("id"))
        )
        return web.json_response(
            {
                "status": "success",
                "file_name": file_data.file_name,
                "file_size": humanbytes(file_data.file_size),
                "mime_type": file_data.mime_type,
                "file_unique_id": file_data.unique_id,
                "file_url": f"{random.choice(Domain.CLOUDFLARE_URLS)}v3/{id.get('id')}?hash={file_data.unique_id[:6]}",
                "store_link": f"https://telegram.me/{Telegram.FILE_STORE_BOT_USERNAME}?start=download_{id.get('id')}",
            },
        )
    except Exception as e:
        logging.error(f"Error processing API request: {str(e)}")
        return web.json_response(
            {"status": "error", "message": "Failed to process the request"}
        )


@routes.get("/status", allow_head=True)
async def status_route_handler(_):
    """
    Enhanced status endpoint with performance metrics and caching information
    """
    try:
        # Import performance monitoring here to avoid circular imports
        from MrAKTech.tools.performance_monitor import performance_monitor
        from MrAKTech.tools.advanced_cache import file_metadata_cache, stream_session_cache, general_cache
        
        # Get bot workloads
        bot_workloads = sorted(work_loads.items(), key=lambda x: x[1], reverse=True)
        total_workload = sum(workload for _, workload in bot_workloads)
        bot_workload_dict = dict(
            ("bot" + str(c + 1), workload) for c, (_, workload) in enumerate(bot_workloads)
        )
        
        # Get performance stats
        perf_stats = performance_monitor.get_performance_summary()
        
        # Get cache statistics
        cache_stats = {
            'file_metadata': file_metadata_cache.get_stats(),
            'stream_sessions': stream_session_cache.get_stats(),
            'general': general_cache.get_stats()
        }
        
        # Calculate overall cache performance
        total_hits = sum(cache['hit_count'] for cache in cache_stats.values())
        total_requests = sum(cache['hit_count'] + cache['miss_count'] for cache in cache_stats.values())
        overall_hit_ratio = (total_hits / total_requests * 100) if total_requests > 0 else 0
        
        return web.json_response({
            "server_status": "running",
            "uptime": readable_time((time.time() - temp.START_TIME)),
            "telegram_bot": "@" + temp.U_NAME,
            "connected_bots": len(multi_clients),
            "loads": bot_workload_dict,
            "TotalLoads": total_workload,
            "version": "V2.0 High-Speed Edition",
            
            # Performance metrics
            "performance": {
                "cpu_usage": f"{perf_stats.get('cpu_usage', 0):.1f}%",
                "memory_usage": f"{perf_stats.get('memory_usage', 0):.1f}%",
                "active_streams": perf_stats.get('active_streams', 0),
                "peak_streams": perf_stats.get('peak_streams', 0),
                "cache_hit_ratio": f"{overall_hit_ratio:.1f}%"
            },
            
            # Cache statistics
            "cache_details": {
                "file_metadata": {
                    "size": cache_stats['file_metadata']['size'],
                    "hit_ratio": f"{cache_stats['file_metadata']['hit_ratio']:.1f}%",
                    "hits": cache_stats['file_metadata']['hit_count']
                },
                "stream_sessions": {
                    "size": cache_stats['stream_sessions']['size'],
                    "hit_ratio": f"{cache_stats['stream_sessions']['hit_ratio']:.1f}%",
                    "hits": cache_stats['stream_sessions']['hit_count']
                }
            },
            
            # Enhanced configuration info
            "optimizations": {
                "workers": Telegram.WORKERS,
                "max_chunk_size": "2MB (dynamic)",
                "caching": "Advanced multi-level",
                "monitoring": "Real-time",
                "features": [
                    "Dynamic chunk sizing",
                    "Advanced caching",
                    "Performance monitoring",
                    "Load balancing",
                    "Enhanced error handling"
                ]
            }
        })
        
    except Exception as e:
        # Fallback to basic status
        bot_workloads = sorted(work_loads.items(), key=lambda x: x[1], reverse=True)
        total_workload = sum(workload for _, workload in bot_workloads)
        bot_workload_dict = dict(
            ("bot" + str(c + 1), workload) for c, (_, workload) in enumerate(bot_workloads)
        )
        
        return web.json_response({
            "server_status": "running",
            "uptime": readable_time((time.time() - temp.START_TIME)),
            "telegram_bot": "@" + temp.U_NAME,
            "connected_bots": len(multi_clients),
            "loads": bot_workload_dict,
            "TotalLoads": total_workload,
            "version": "V2.0 High-Speed Edition",
            "note": "Advanced metrics temporarily unavailable"
        })


@routes.get(r"/watch/{path:\S+}", allow_head=True)
async def stream_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        match = re.search(r"^([a-zA-Z0-9_-]{6})(\d+)$", path)
        if match:
            secure_hash = match.group(1)
            message_id = int(match.group(2))
        else:
            message_id = int(re.search(r"(\d+)(?:\/\S+)?", path).group(1))
            secure_hash = request.rel_url.query.get("hash")
        return web.Response(
            text=await render_page(message_id, secure_hash), content_type="text/html"
        )
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError):
        pass
    except Exception as e:
        logger.critical(str(e), exc_info=True)
        raise web.HTTPInternalServerError(text=str(e))


@routes.get(r"/dl/{path:\S+}", allow_head=True)
async def dl_stream_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        match = re.search(r"^([a-zA-Z0-9_-]{6})(\d+)$", path)
        if match:
            secure_hash = match.group(1)
            message_id = int(match.group(2))
        else:
            message_id = int(re.search(r"(\d+)(?:\/\S+)?", path).group(1))
            secure_hash = request.rel_url.query.get("hash")
        return await media_streamer(request, message_id, secure_hash)
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError):
        pass
    except Exception as e:
        logger.critical(str(e), exc_info=True)
        raise web.HTTPInternalServerError(text=str(e))


@routes.get(r"/v2/{path:\S+}", allow_head=True)
async def v2_stream_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        return await media_streamer(request, message_id=int(path[6:]), secure_hash=str(path[:6]))
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError):
        pass
    except Exception as e:
        logger.critical(str(e), exc_info=True)
        raise web.HTTPInternalServerError(text=str(e))


@routes.get(r"/v3/{path:\S+}", allow_head=True)
async def v3_stream_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        return await media_streamer(request, message_id=int(path[6:]), secure_hash=str(path[:6]))
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError):
        pass
    except Exception as e:
        logger.critical(str(e), exc_info=True)
        raise web.HTTPInternalServerError(text=str(e))


class_cache = {}


async def media_streamer(request: web.Request, message_id: int, secure_hash: str):
    """
    Optimized media streamer with enhanced performance and caching
    """
    range_header = request.headers.get("Range", 0)
    
    # Get the least loaded client for optimal performance
    index = min(work_loads, key=work_loads.get)
    faster_client = multi_clients[index]

    # Enhanced caching system
    if faster_client in class_cache:
        tg_connect = class_cache[faster_client]
        logger.debug(f"Using cached ByteStreamer object for client {index}")
    else:
        logger.debug(f"Creating new ByteStreamer object for client {index}")
        tg_connect = ByteStreamer(faster_client)
        class_cache[faster_client] = tg_connect
    
    logger.debug("before calling get_file_properties")
    file_id = await tg_connect.get_file_properties(message_id)
    logger.debug("after calling get_file_properties")
    
    # Security validation
    if file_id.unique_id[:6] != secure_hash:
        logger.debug(f"Invalid hash for message with ID {message_id}")
        raise InvalidHash

    file_size = file_id.file_size

    # Optimized range handling for better streaming
    if range_header:
        from_bytes, until_bytes = range_header.replace("bytes=", "").split("-")
        from_bytes = int(from_bytes)
        until_bytes = int(until_bytes) if until_bytes else file_size - 1
    else:
        from_bytes = request.http_range.start or 0
        until_bytes = request.http_range.stop or file_size - 1

    # Enhanced chunk size calculation for better performance
    req_length = until_bytes - from_bytes
    new_chunk_size = await chunk_size(req_length)
    offset = await offset_fix(from_bytes, new_chunk_size)
    first_part_cut = from_bytes - offset
    last_part_cut = (until_bytes % new_chunk_size) + 1
    part_count = math.ceil(req_length / new_chunk_size)
    
    # Create the streaming body
    body = tg_connect.yield_file(
        file_id, index, offset, first_part_cut, last_part_cut, part_count, new_chunk_size
    )

    # Enhanced MIME type detection and file handling
    mime_type = file_id.mime_type
    file_name = file_id.file_name
    disposition = "attachment"
    
    if mime_type:
        if not file_name:
            try:
                file_name = f"{secrets.token_hex(2)}.{mime_type.split('/')[1]}"
            except (IndexError, AttributeError):
                file_name = f"{secrets.token_hex(2)}.unknown"
    else:
        if file_name:
            mime_type = mimetypes.guess_type(file_id.file_name)[0] or "application/octet-stream"
        else:
            mime_type = "application/octet-stream"
            file_name = f"{secrets.token_hex(2)}.unknown"
    
    # Optimized response headers for better streaming and caching
    headers = {
        "Content-Type": f"{mime_type}",
        "Accept-Ranges": "bytes",
        "Content-Disposition": f'{disposition}; filename="{file_name}"',
        "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
        "ETag": f'"{file_id.unique_id}"',  # Enable ETag for better caching
        "X-Accel-Buffering": "no",  # Disable proxy buffering for better streaming
        "X-Content-Type-Options": "nosniff",  # Security header
    }
    
    # Add range-specific headers
    if range_header:
        headers.update({
            "Content-Range": f"bytes {from_bytes}-{until_bytes}/{file_size}",
            "Content-Length": str(req_length + 1),
        })
        status = 206
    else:
        headers["Content-Length"] = str(file_size)
        status = 200

    return_resp = web.Response(
        status=status,
        body=body,
        headers=headers,
    )

    return return_resp


async def get_channel_verify_shortlink_to_use(channel_settings, verify_count):
    """Determine which channel verify shortlink should be used based on verification count"""
    verify_shortlinks = channel_settings.get('verify_shortlinks', {
        "shortlink1": {"url": None, "api": None},
        "shortlink2": {"url": None, "api": None},
        "shortlink3": {"url": None, "api": None}
    })
    
    # Logic: Start with shortlink3, then shortlink2, then shortlink1, then direct
    if verify_count == 0:
        # First verification - use shortlink3 if available
        if verify_shortlinks["shortlink3"]["url"] and verify_shortlinks["shortlink3"]["api"]:
            return "shortlink3", verify_shortlinks["shortlink3"]
    elif verify_count == 1:
        # Second verification - use shortlink2 if available
        if verify_shortlinks["shortlink2"]["url"] and verify_shortlinks["shortlink2"]["api"]:
            return "shortlink2", verify_shortlinks["shortlink2"]
    elif verify_count == 2:
        # Third verification - use shortlink1 if available
        if verify_shortlinks["shortlink1"]["url"] and verify_shortlinks["shortlink1"]["api"]:
            return "shortlink1", verify_shortlinks["shortlink1"]
    
    # If we've done 3+ verifications or no shortlinks configured, go direct
    return "direct", None


@routes.get("/sl/{message_id}/{page_code}", allow_head=True)
async def shortlink_page_handler(request):
    """Handle shortlink page display"""
    try:
        message_id = request.match_info["message_id"]
        page_code = request.match_info["page_code"]
        
        # Check if this is a channel request
        channel_id = request.query.get("channel", None)
        
        # Get user/channel settings by page code
        from MrAKTech.database.u_db import u_db
        
        if channel_id:
            # Channel context - verify page code belongs to this channel
            channel = await u_db.get_channel_by_page_code(page_code)
            if not channel or str(channel["chat_id"]) != str(channel_id):
                return web.Response(text="Invalid page code for channel", status=404)
            user_id = channel["user_id"]  # Get channel owner
        else:
            # User context - get user by page code
            user = await u_db.get_user_by_page_code(page_code)
            if not user:
                return web.Response(text="Invalid page code", status=404)
            user_id = user["id"]
        
        # Get page mode settings and shortlinks based on context
        if channel_id:
            # Channel context
            channel_id = int(channel_id)
            page_mode = await u_db.get_chl_page_mode(channel_id)
            # Get channel settings for verify mode check
            channel_settings = await u_db.get_chl_settings(channel_id)
            verify_mode = channel_settings.get('verify_mode', False)
        else:
            # User context
            page_mode = await u_db.get_page_mode(user_id)
            verify_mode = await u_db.get_verify_mode(user_id)
        
        if not page_mode:
            # If page mode is disabled, redirect to direct stream link
            return web.HTTPFound(f"/watch/{message_id}")

        # **SMART SHORTLINK SELECTION LOGIC**
        # If verify mode is enabled, use verify shortlinks; otherwise use page shortlinks
        if verify_mode:
            # Use verify shortlinks when verify mode is enabled
            if channel_id:
                page_shortlinks = channel_settings.get('verify_shortlinks', {
                    "shortlink1": {"url": None, "api": None},
                    "shortlink2": {"url": None, "api": None},
                    "shortlink3": {"url": None, "api": None}
                })
                # Get verify settings for customization
                verify_settings = channel_settings.get('verify_settings', {
                    "shortlink_tutorials": {
                        "shortlink1": {"enabled": False, "video_url": None, "button_text": "📺 Verify Tutorial"},
                        "shortlink2": {"enabled": False, "video_url": None, "button_text": "📺 Verify Tutorial"},
                        "shortlink3": {"enabled": False, "video_url": None, "button_text": "📺 Verify Tutorial"}
                    }
                })
                # Get page settings for button customization (used even in verify mode)
                page_settings = channel_settings.get('page_settings', {
                    "button_visibility": {"watch": True, "download": True, "telegram": True},
                    "button_names": {"watch": "🎮 Watch Online", "download": "📥 Download", "telegram": "📱 Telegram Storage"},
                    "custom_buttons": []
                })
            else:
                page_shortlinks = await u_db.get_verify_shortlinks(user_id)
                verify_settings = await u_db.get_verify_settings(user_id)
                page_settings = await u_db.get_page_settings(user_id)
        else:
            # Use regular page shortlinks when verify mode is disabled
            if channel_id:
                page_shortlinks = await u_db.get_chl_page_shortlinks(channel_id)
                page_settings = await u_db.get_chl_page_settings(channel_id)
                verify_settings = None
            else:
                page_shortlinks = await u_db.get_page_shortlinks(user_id)
                page_settings = await u_db.get_page_settings(user_id)
                verify_settings = None

        # Check verify mode functionality (keep existing verification logic)
        verify_required = False
        verification_data = {}
        
        if verify_mode:
            # Get verification status (always use user_id for visitor verification tracking)
            verification_status = await u_db.get_verification_status(user_id)
            verify_count_today = verification_status.get("verify_count_today", 0)
            
            # Check if user needs verification today
            is_verified_today = await u_db.is_user_verified_today(user_id)
            
            # Get which shortlink to use for verification based on context
            if channel_id:
                # Channel context: use channel's verify shortlinks but track user verification
                shortlink_type, shortlink_config = await get_channel_verify_shortlink_to_use(channel_settings, verify_count_today)
            else:
                # User context: use user's verify shortlinks
                shortlink_type, shortlink_config = await u_db.get_verify_shortlink_to_use(user_id)
            
            if shortlink_type != "direct" and shortlink_config:
                verify_required = True
                
                # Determine verification step and message
                if verify_count_today == 0:
                    verify_step = 1
                    verification_message = "First verification of the day required"
                elif verify_count_today == 1:
                    verify_step = 2
                    verification_message = "Second verification required"
                elif verify_count_today == 2:
                    verify_step = 3
                    verification_message = "Final verification required"
                else:
                    verify_step = verify_count_today + 1
                    verification_message = f"Verification {verify_step} required"
                
                # Generate verification link
                from MrAKTech.tools.utils_bot import short_link_with_custom_shortener
                
                # Create a special verification URL that will mark user as verified
                # Include channel info in callback URL for proper redirect
                if channel_id:
                    verify_callback_url = f"{Server.URL}/verify/{user_id}/{message_id}/{shortlink_type}?channel={channel_id}"
                else:
                    verify_callback_url = f"{Server.URL}/verify/{user_id}/{message_id}/{shortlink_type}"
                
                try:
                    verify_link = await short_link_with_custom_shortener(
                        verify_callback_url,
                        shortlink_config["url"],
                        shortlink_config["api"]
                    )
                except Exception as e:
                    logger.error(f"Error creating verification shortlink: {e}")
                    verify_link = verify_callback_url
                
                verification_data = {
                    "verify_required": True,
                    "verification_message": verification_message,
                    "verify_count_today": verify_count_today,
                    "remaining_verifications": max(0, 3 - verify_count_today),
                    "verify_step": verify_step,
                    "verify_link": verify_link,
                    "max_verifications": 3
                }
        
        # Get file information using the same method as other routes
        try:
            file_data = await get_file_ids(StreamBot, int(Telegram.FLOG_CHANNEL), int(message_id))
            if not file_data:
                return web.Response(text="File not found", status=404)
            
            file_name = file_data.file_name or "Unknown File"
            file_size = humanbytes(file_data.file_size)
        except Exception as e:
            logger.error(f"Error getting file data: {e}")
            return web.Response(text="File not found", status=404)
        
        # Extract metadata
        from MrAKTech.tools.extract_info import extract_quality, extract_season_number, extract_episode_number
        quality = extract_quality(file_name)
        season = extract_season_number(file_name) if hasattr(extract_quality, '__module__') else None
        episode = extract_episode_number(file_name) if hasattr(extract_quality, '__module__') else None
        
        # Build context for template
        class ShortlinkData:
            def __init__(self):
                self.shortlink1 = type('obj', (object,), {'url': None, 'watch_link': None, 'download_link': None, 'storage_link': None})()
                self.shortlink2 = type('obj', (object,), {'url': None, 'watch_link': None, 'download_link': None, 'storage_link': None})()
                self.shortlink3 = type('obj', (object,), {'url': None, 'watch_link': None, 'download_link': None, 'storage_link': None})()
        
        shortlinks_obj = ShortlinkData()
        
        context = {
            "file_name": file_name,
            "file_size": file_size,
            "quality": quality if quality else None,
            "duration": None,  # Can be added later if needed
            "error_message": None,
            "shortlinks": shortlinks_obj,
            "direct_links": {},
            "auto_redirect": False,
            "custom_buttons": page_settings.get("custom_buttons", []),
            "verification_data": verification_data, # Add verification data to context
            "page_settings": page_settings, # Pass page settings
            "verify_settings": verify_settings # Pass verify settings
        }
        
        # Merge verification data directly into context
        context.update(verification_data)
        
        # Import shortlink function
        from MrAKTech.tools.utils_bot import short_link_with_custom_shortener
        
        # Process shortlinks with domain names and tutorial data
        for i in range(1, 4):
            shortlink_data = page_shortlinks.get(f"shortlink{i}", {})
            if shortlink_data.get("url") and shortlink_data.get("api"):
                
                # Get the actual file message to generate hash
                try:
                    from MrAKTech.tools.file_properties import get_hash
                    file_msg = await StreamBot.get_messages(chat_id=int(Telegram.FLOG_CHANNEL), message_ids=int(message_id))
                    file_hash = get_hash(file_msg)
                except Exception as e:
                    logger.error(f"Error getting file hash: {e}")
                    file_hash = ""
                
                # Generate base links with proper hash and format
                watch_url = f"{Server.URL}/watch/{message_id}?hash={file_hash}"
                download_url = f"{Server.URL}/dl/{message_id}?hash={file_hash}"
                storage_url = f"https://telegram.me/{Telegram.FILE_STORE_BOT_USERNAME}?start=download_{message_id}"
                
                # Apply shortlinks
                try:
                    watch_short = await short_link_with_custom_shortener(
                        watch_url, 
                        shortlink_data["url"], 
                        shortlink_data["api"]
                    )
                    download_short = await short_link_with_custom_shortener(
                        download_url, 
                        shortlink_data["url"], 
                        shortlink_data["api"]
                    )
                    storage_short = await short_link_with_custom_shortener(
                        storage_url, 
                        shortlink_data["url"], 
                        shortlink_data["api"]
                    )
                    
                    # Set the shortlink data on the object with domain name
                    shortlink_obj = getattr(context["shortlinks"], f"shortlink{i}")
                    shortlink_obj.url = shortlink_data["url"]
                    shortlink_obj.domain_name = shortlink_data["url"]  # Domain name for heading
                    shortlink_obj.watch_link = watch_short
                    shortlink_obj.download_link = download_short
                    shortlink_obj.storage_link = storage_short
                    
                    # Add tutorial data if available
                    if verify_mode and verify_settings:
                        tutorial_data = verify_settings.get("shortlink_tutorials", {}).get(f"shortlink{i}", {})
                    else:
                        tutorial_data = page_settings.get("shortlink_tutorials", {}).get(f"shortlink{i}", {})
                    
                    shortlink_obj.tutorial_enabled = tutorial_data.get("enabled", False)
                    shortlink_obj.tutorial_url = tutorial_data.get("video_url", None)
                    shortlink_obj.tutorial_text = tutorial_data.get("button_text", "📺 Tutorial")
                    
                except Exception as e:
                    logger.error(f"Error creating shortlink: {e}")
                    context["error_message"] = f"Error with shortlink {i}. Please try again later."
        
        # If no shortlinks are configured, provide direct links
        if not any([context["shortlinks"].shortlink1.url, context["shortlinks"].shortlink2.url, context["shortlinks"].shortlink3.url]):
            # Generate hash for direct links as well
            try:
                from MrAKTech.tools.file_properties import get_hash
                file_msg = await StreamBot.get_messages(chat_id=int(Telegram.FLOG_CHANNEL), message_ids=int(message_id))
                file_hash = get_hash(file_msg)
            except Exception as e:
                logger.error(f"Error getting file hash for direct links: {e}")
                file_hash = ""
            
            context["direct_links"] = {
                "watch_link": f"{Server.URL}/watch/{message_id}?hash={file_hash}",
                "download_link": f"{Server.URL}/dl/{message_id}?hash={file_hash}",
                "storage_link": f"https://telegram.me/{Telegram.FILE_STORE_BOT_USERNAME}?start=download_{message_id}"
            }
        
        # Render the shortlink page
        try:
            # Use the existing render_template approach
            from jinja2 import Environment, FileSystemLoader
            import os
            
            # Get the template directory
            template_dir = os.path.join("MrAKTech", "server", "template")
            env = Environment(loader=FileSystemLoader(template_dir))
            template = env.get_template("shortlink.html")
            
            rendered_html = template.render(**context)
            
            return web.Response(
                text=rendered_html,
                content_type="text/html"
            )
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            # Fallback to simple HTML response
            return web.Response(
                text=f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Shortlink Page</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                </head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1>File Access</h1>
                    <p><strong>File:</strong> {context.get('file_name', 'Unknown')}</p>
                    <p><strong>Size:</strong> {context.get('file_size', 'Unknown')}</p>
                    <div style="margin: 20px;">
                        <a href="{context.get('direct_links', {}).get('watch_link', '#')}" 
                           style="display: inline-block; margin: 10px; padding: 10px 20px; 
                                  background: #007bff; color: white; text-decoration: none; 
                                  border-radius: 5px;">Watch Online</a>
                        <a href="{context.get('direct_links', {}).get('download_link', '#')}" 
                           style="display: inline-block; margin: 10px; padding: 10px 20px; 
                                  background: #28a745; color: white; text-decoration: none; 
                                  border-radius: 5px;">Download</a>
                        <a href="{context.get('direct_links', {}).get('storage_link', '#')}" 
                           style="display: inline-block; margin: 10px; padding: 10px 20px; 
                                  background: #17a2b8; color: white; text-decoration: none; 
                                  border-radius: 5px;">Telegram Storage</a>
                    </div>
                    <p style="color: red;">Template Error: {str(e)}</p>
                </body>
                </html>
                """,
                content_type="text/html",
                status=500
            )
        
    except Exception as e:
        logger.error(f"Error in shortlink page: {e}")
        import traceback
        traceback.print_exc()
        return web.Response(text="Internal server error", status=500)


@routes.get("/verify/{user_id}/{message_id}/{shortlink_type}", allow_head=True)
async def verify_completion_handler(request):
    """Handle verification completion and redirect to actual file"""
    try:
        user_id = int(request.match_info["user_id"])
        message_id = request.match_info["message_id"]
        shortlink_type = request.match_info["shortlink_type"]
        
        from MrAKTech.database.u_db import u_db
        
        # Mark user as verified
        await u_db.mark_user_verified(user_id, "last")
        
        # Get file information for redirect
        try:
            from MrAKTech.tools.file_properties import get_hash
            file_msg = await StreamBot.get_messages(chat_id=int(Telegram.FLOG_CHANNEL), message_ids=int(message_id))
            file_hash = get_hash(file_msg)
        except Exception as e:
            logger.error(f"Error getting file hash for verification redirect: {e}")
            file_hash = ""
        
        # Determine redirect URL based on context
        channel_id = request.query.get("channel", None)
        if channel_id:
            # Channel context - redirect back to channel page
            channel = await u_db.get_channel_by_page_code(await u_db.get_chl_page_code(int(channel_id)))
            if channel:
                page_code = channel.get("page_code")
                redirect_url = f"{Server.URL}/sl/{message_id}/{page_code}?channel={channel_id}"
            else:
                # Fallback to user's page if channel not found
                redirect_url = f"{Server.URL}/sl/{message_id}/{await u_db.get_page_code(user_id)}"
        else:
            # User context - redirect to user's page
            redirect_url = f"{Server.URL}/sl/{message_id}/{await u_db.get_page_code(user_id)}"
        
        # Create a success page with auto-redirect
        success_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verification Complete</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0;
                    color: white;
                }}
                .container {{
                    text-align: center;
                    background: rgba(255, 255, 255, 0.1);
                    padding: 2rem;
                    border-radius: 20px;
                    backdrop-filter: blur(20px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }}
                .success-icon {{
                    font-size: 4rem;
                    margin-bottom: 1rem;
                }}
                .loading {{
                    display: inline-block;
                    width: 20px;
                    height: 20px;
                    border: 3px solid #f3f3f3;
                    border-top: 3px solid #667eea;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-left: 10px;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon">✅</div>
                <h1>Verification Complete!</h1>
                <p>Thank you for completing the verification.</p>
                <p>Redirecting you to your file... <span class="loading"></span></p>
                <p><a href="{redirect_url}" style="color: #4facfe;">Click here if not redirected automatically</a></p>
            </div>
            
            <script>
                setTimeout(function() {{
                    window.location.href = "{redirect_url}";
                }}, 3000);
            </script>
        </body>
        </html>
        """
        
        return web.Response(text=success_html, content_type="text/html")
        
    except Exception as e:
        logger.error(f"Error in verification handler: {e}")
        return web.Response(text="Verification error", status=500)


class_cache = {}
