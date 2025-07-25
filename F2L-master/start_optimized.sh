#!/bin/bash

# High-Performance MrAK Streaming Bot Startup Script
# Copyright 2021 To 2024-present, Author: MrAKTech

echo "=================================="
echo "🚀 MrAK High-Speed Streaming Bot"
echo "=================================="

# Function to check if running on Linux
check_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "✅ Linux detected - applying performance optimizations"
        return 0
    else
        echo "⚠️  Non-Linux OS detected - some optimizations may not apply"
        return 1
    fi
}

# Function to optimize system for high performance
optimize_system() {
    echo "🔧 Applying system optimizations..."
    
    # Increase file descriptor limits
    ulimit -n 65536
    echo "📁 File descriptor limit set to 65536"
    
    # Optimize TCP settings for better streaming
    if check_os; then
        # These settings work on Linux
        echo "🌐 Optimizing network settings..."
        
        # TCP window scaling
        echo 'net.core.rmem_max = 134217728' | sudo tee -a /etc/sysctl.conf
        echo 'net.core.wmem_max = 134217728' | sudo tee -a /etc/sysctl.conf
        echo 'net.ipv4.tcp_rmem = 4096 16384 134217728' | sudo tee -a /etc/sysctl.conf
        echo 'net.ipv4.tcp_wmem = 4096 16384 134217728' | sudo tee -a /etc/sysctl.conf
        
        # Connection tracking
        echo 'net.netfilter.nf_conntrack_max = 1000000' | sudo tee -a /etc/sysctl.conf
        echo 'net.core.netdev_max_backlog = 5000' | sudo tee -a /etc/sysctl.conf
        
        sudo sysctl -p
        echo "✅ Network optimizations applied"
    fi
    
    # Set CPU governor to performance mode
    if command -v cpufreq-set &> /dev/null; then
        sudo cpufreq-set -g performance
        echo "⚡ CPU governor set to performance mode"
    fi
}

# Function to install performance packages
install_performance_packages() {
    echo "📦 Installing performance packages..."
    
    # Update pip
    python3 -m pip install --upgrade pip
    
    # Install requirements with optimizations
    python3 -m pip install -r requirements.txt --upgrade
    
    # Install additional performance packages
    python3 -m pip install uvloop orjson aiodns cchardet brotlipy lz4
    
    echo "✅ Performance packages installed"
}

# Function to create optimized environment file
create_optimized_env() {
    echo "⚙️  Creating optimized environment configuration..."
    
    cat > .env.performance << 'EOF'
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
EOF

    echo "✅ Performance environment file created (.env.performance)"
    echo "💡 Add these settings to your main .env file for optimal performance"
}

# Function to start the bot with optimizations
start_bot() {
    echo "🚀 Starting MrAK High-Speed Streaming Bot..."
    
    # Set environment variables for performance
    export PYTHONUNBUFFERED=1
    export PYTHONOPTIMIZE=2
    export PYTHONASYNCIODEBUG=0
    
    # Use uvloop if available (Linux/macOS only)
    if check_os; then
        export PYTHONPATH="${PYTHONPATH}:."
        python3 -c "import uvloop; uvloop.install()" 2>/dev/null && echo "✅ uvloop installed for better async performance"
    fi
    
    # Start the bot
    echo "▶️  Launching bot with high-performance settings..."
    python3 -m MrAKTech
}

# Function to monitor performance
monitor_performance() {
    echo "📊 Performance Monitoring Available:"
    echo "   - CPU Usage: htop or top"
    echo "   - Network: iftop or nethogs"
    echo "   - Memory: free -h"
    echo "   - Bot Stats: Available in bot interface"
}

# Main execution
main() {
    echo "🔍 Checking system requirements..."
    
    # Check Python version
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo "🐍 Python version: $python_version"
    
    if [[ "$1" == "--optimize" ]]; then
        optimize_system
    fi
    
    if [[ "$1" == "--install" ]]; then
        install_performance_packages
    fi
    
    if [[ "$1" == "--env" ]]; then
        create_optimized_env
        exit 0
    fi
    
    if [[ "$1" == "--monitor" ]]; then
        monitor_performance
        exit 0
    fi
    
    # Default: start the bot
    start_bot
}

# Handle script arguments
case "$1" in
    --help|-h)
        echo "Usage: $0 [option]"
        echo "Options:"
        echo "  --optimize    Apply system optimizations"
        echo "  --install     Install performance packages"
        echo "  --env         Create optimized environment file"
        echo "  --monitor     Show monitoring commands"
        echo "  --help        Show this help"
        echo "  (no args)     Start the bot"
        ;;
    *)
        main "$@"
        ;;
esac
