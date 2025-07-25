# High-Performance MrAK Streaming Bot Startup Script for Windows
# Copyright 2021 To 2024-present, Author: MrAKTech

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "🚀 MrAK High-Speed Streaming Bot" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

function Show-Banner {
    Write-Host ""
    Write-Host "Performance Optimizations:" -ForegroundColor Yellow
    Write-Host "  ✅ Enhanced chunk sizing for better streaming" -ForegroundColor Green
    Write-Host "  ✅ Advanced caching system" -ForegroundColor Green
    Write-Host "  ✅ Optimized server configuration" -ForegroundColor Green
    Write-Host "  ✅ Performance monitoring" -ForegroundColor Green
    Write-Host "  ✅ 16 workers for maximum throughput" -ForegroundColor Green
    Write-Host ""
}

function Install-PerformancePackages {
    Write-Host "📦 Installing performance packages..." -ForegroundColor Blue
    
    # Update pip
    python -m pip install --upgrade pip
    
    # Install requirements with optimizations
    python -m pip install -r requirements.txt --upgrade
    
    # Install additional performance packages
    python -m pip install orjson aiodns cchardet brotlipy lz4
    
    Write-Host "✅ Performance packages installed" -ForegroundColor Green
}

function Create-OptimizedEnv {
    Write-Host "⚙️  Creating optimized environment configuration..." -ForegroundColor Blue
    
    $envContent = @"
# High-Performance Configuration for MrAK Bot

# Enhanced Worker Configuration
WORKERS=16
MAX_CONCURRENT_TRANSMISSIONS=8
CHUNK_SIZE=2097152
CACHE_TIME=1800

# Server Optimization
MAX_CONNECTIONS=1000
KEEPALIVE_TIMEOUT=75
CLIENT_TIMEOUT=300
BUFFER_SIZE=65536
PING_INTERVAL=300

# Memory and Performance
SLEEP_THRESHOLD=30

# Python Optimizations
PYTHONUNBUFFERED=1
PYTHONOPTIMIZE=2

# asyncio optimizations
PYTHONASYNCIODEBUG=0
"@

    $envContent | Out-File -FilePath ".env.performance" -Encoding UTF8
    
    Write-Host "✅ Performance environment file created (.env.performance)" -ForegroundColor Green
    Write-Host "💡 Add these settings to your main .env file for optimal performance" -ForegroundColor Yellow
}

function Start-Bot {
    Write-Host "🚀 Starting MrAK High-Speed Streaming Bot..." -ForegroundColor Blue
    
    # Set environment variables for performance
    $env:PYTHONUNBUFFERED = "1"
    $env:PYTHONOPTIMIZE = "2"
    $env:PYTHONASYNCIODEBUG = "0"
    
    # Start the bot
    Write-Host "▶️  Launching bot with high-performance settings..." -ForegroundColor Green
    python -m MrAKTech
}

function Show-MonitoringInfo {
    Write-Host "📊 Performance Monitoring Available:" -ForegroundColor Blue
    Write-Host "   - Task Manager for CPU/Memory monitoring" -ForegroundColor White
    Write-Host "   - Resource Monitor for detailed system stats" -ForegroundColor White
    Write-Host "   - Bot Stats: Available in bot interface" -ForegroundColor White
    Write-Host "   - Performance logs in BotLog.txt" -ForegroundColor White
}

function Show-Help {
    Write-Host "Usage: .\start_optimized.ps1 [option]" -ForegroundColor Yellow
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  -Install      Install performance packages" -ForegroundColor White
    Write-Host "  -Env          Create optimized environment file" -ForegroundColor White
    Write-Host "  -Monitor      Show monitoring commands" -ForegroundColor White
    Write-Host "  -Help         Show this help" -ForegroundColor White
    Write-Host "  (no args)     Start the bot" -ForegroundColor White
}

function Check-Requirements {
    Write-Host "🔍 Checking system requirements..." -ForegroundColor Blue
    
    # Check Python version
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "🐍 $pythonVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Python not found. Please install Python 3.8+" -ForegroundColor Red
        exit 1
    }
    
    # Check if requirements.txt exists
    if (-not (Test-Path "requirements.txt")) {
        Write-Host "❌ requirements.txt not found" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Requirements check passed" -ForegroundColor Green
}

# Main execution based on parameters
param(
    [switch]$Install,
    [switch]$Env,
    [switch]$Monitor,
    [switch]$Help
)

Show-Banner

if ($Help) {
    Show-Help
    exit 0
}

if ($Install) {
    Check-Requirements
    Install-PerformancePackages
    exit 0
}

if ($Env) {
    Create-OptimizedEnv
    exit 0
}

if ($Monitor) {
    Show-MonitoringInfo
    exit 0
}

# Default: Check requirements and start the bot
Check-Requirements
Write-Host ""
Write-Host "🎯 Quick Setup Commands:" -ForegroundColor Magenta
Write-Host "   .\start_optimized.ps1 -Install    # Install performance packages" -ForegroundColor White
Write-Host "   .\start_optimized.ps1 -Env        # Create optimized .env file" -ForegroundColor White
Write-Host ""

Start-Bot
