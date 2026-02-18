#!/bin/bash
# Dalio Lite - Auto-Pilot Setup Script
# Sets up daily automated portfolio checks

set -e

echo "🚀 Dalio Lite Auto-Pilot Setup"
echo "================================"
echo ""

# Get the current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_PATH=$(which python3)

# Verify Python exists
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ Error: Python 3 not found"
    echo "Install Python 3 and try again"
    exit 1
fi

# Verify dalio_lite.py exists
if [ ! -f "$SCRIPT_DIR/dalio_lite.py" ]; then
    echo "❌ Error: dalio_lite.py not found in $SCRIPT_DIR"
    exit 1
fi

# Ask for notification preferences
echo "📧 Email Notifications Setup"
echo "----------------------------"
read -p "Enable email notifications? (y/n): " ENABLE_EMAIL

if [ "$ENABLE_EMAIL" = "y" ]; then
    read -p "Your email address: " USER_EMAIL

    # Create notification config
    cat > "$SCRIPT_DIR/.notification_config" << EOF
ENABLE_EMAIL=true
USER_EMAIL=$USER_EMAIL
EOF

    echo "✅ Email notifications enabled for: $USER_EMAIL"
    echo ""
    echo "⚠️  Note: You'll need to configure SendGrid API key for email delivery"
    echo "   Set SENDGRID_API_KEY in your .env file"
else
    cat > "$SCRIPT_DIR/.notification_config" << EOF
ENABLE_EMAIL=false
USER_EMAIL=
EOF
    echo "📭 Email notifications disabled"
fi

echo ""
echo "⏰ Schedule Setup"
echo "----------------------------"
echo "When should the daily check run?"
echo "1) 9:00 AM (recommended - after market open)"
echo "2) 6:00 PM (after market close)"
echo "3) Custom time"
read -p "Choose (1-3): " TIME_CHOICE

case $TIME_CHOICE in
    1)
        HOUR=9
        MINUTE=0
        ;;
    2)
        HOUR=18
        MINUTE=0
        ;;
    3)
        read -p "Hour (0-23): " HOUR
        read -p "Minute (0-59): " MINUTE
        ;;
    *)
        echo "Invalid choice. Defaulting to 9:00 AM"
        HOUR=9
        MINUTE=0
        ;;
esac

echo ""
echo "📅 Setting up daily check at $HOUR:$(printf "%02d" $MINUTE)"

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS - use launchd
    echo "Detected macOS - using launchd"

    PLIST_FILE="$HOME/Library/LaunchAgents/com.daliolite.autopilot.plist"

    cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.daliolite.autopilot</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>$SCRIPT_DIR/dalio_lite.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>$HOUR</integer>
        <key>Minute</key>
        <integer>$MINUTE</integer>
    </dict>
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
    <key>StandardOutPath</key>
    <string>$SCRIPT_DIR/logs/autopilot.log</string>
    <key>StandardErrorPath</key>
    <string>$SCRIPT_DIR/logs/autopilot_error.log</string>
</dict>
</plist>
EOF

    # Load the job
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
    launchctl load "$PLIST_FILE"

    echo "✅ Auto-Pilot scheduled with launchd"
    echo "   Location: $PLIST_FILE"

elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux - use cron
    echo "Detected Linux - using cron"

    CRON_CMD="$MINUTE $HOUR * * * cd $SCRIPT_DIR && $PYTHON_PATH dalio_lite.py >> $SCRIPT_DIR/logs/autopilot.log 2>&1"

    # Add to crontab (checking if it already exists)
    (crontab -l 2>/dev/null | grep -v "dalio_lite.py"; echo "$CRON_CMD") | crontab -

    echo "✅ Auto-Pilot scheduled with cron"
    echo "   Command: $CRON_CMD"
else
    echo "❌ Unsupported OS: $OSTYPE"
    echo "Please set up scheduling manually"
    exit 1
fi

# Create autopilot status file
cat > "$SCRIPT_DIR/state/autopilot_status.json" << EOF
{
    "enabled": true,
    "schedule": "$HOUR:$(printf "%02d" $MINUTE)",
    "notifications": $([ "$ENABLE_EMAIL" = "y" ] && echo "true" || echo "false"),
    "email": "$USER_EMAIL",
    "setup_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF

echo ""
echo "✅ AUTO-PILOT SETUP COMPLETE!"
echo "================================"
echo ""
echo "📋 Summary:"
echo "  • Daily check scheduled: $HOUR:$(printf "%02d" $MINUTE)"
echo "  • Email notifications: $([ "$ENABLE_EMAIL" = "y" ] && echo "Enabled ($USER_EMAIL)" || echo "Disabled")"
echo "  • Logs: $SCRIPT_DIR/logs/autopilot.log"
echo ""
echo "🎯 Next Steps:"
echo "  1. System will run automatically every day"
echo "  2. Check logs to verify first run"
echo "  3. You'll receive email summary (if enabled)"
echo ""
echo "🛑 To disable Auto-Pilot:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "  launchctl unload $PLIST_FILE"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "  crontab -e  (and remove the dalio_lite line)"
fi
echo ""
echo "✨ You can now forget about your portfolio!"
