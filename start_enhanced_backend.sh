#!/bin/bash
# Enhanced Nintendo Switch Parental Controls Startup Script
# For Raspberry Pi deployment

BACKEND_DIR="/home/pi/parental-controls"
BACKEND_SCRIPT="pi_enhanced_backend_8446.py"
LOG_FILE="enhanced_backend.log"

cd "$BACKEND_DIR"

echo "🚀 Starting Enhanced Nintendo Switch Parental Controls Backend..."
echo "📁 Working directory: $(pwd)"
echo "🎮 Backend script: $BACKEND_SCRIPT"
echo "📝 Log file: $LOG_FILE"

# Check if already running
if pgrep -f "$BACKEND_SCRIPT" > /dev/null; then
    echo "⚠️  Backend is already running!"
    echo "📊 Process IDs: $(pgrep -f "$BACKEND_SCRIPT" | tr '\n' ' ')"
    echo "🔗 Dashboard: http://192.168.123.7:8446"
    exit 1
fi

# Start the backend
echo "▶️  Starting backend process..."
nohup python3 "$BACKEND_SCRIPT" > "$LOG_FILE" 2>&1 &
BACKEND_PID=$!

# Wait a moment and check if it started
sleep 3

if pgrep -f "$BACKEND_SCRIPT" > /dev/null; then
    echo "✅ Enhanced Backend started successfully!"
    echo "📊 Process ID: $BACKEND_PID"
    echo "🔗 Dashboard: http://192.168.123.7:8446"
    echo "❤️  Health Check: http://192.168.123.7:8446/health"
    echo "📝 Log file: $BACKEND_DIR/$LOG_FILE"
    echo ""
    echo "🎮 Nintendo Switch devices managed:"
    echo "   • newswitch (192.168.123.134) - Main Gaming Area" 
    echo "   • backroom (192.168.123.135) - Back Room"
    echo ""
    echo "🌟 Features: Enhanced Discovery, Real-time Monitoring, Individual Controls"
else
    echo "❌ Failed to start enhanced backend!"
    echo "📝 Check log file: $LOG_FILE"
    exit 1
fi
