#!/bin/bash

# Claude notification script - alerts when Claude needs interaction
# Uses macOS native notifications

# Read the notification from stdin
notification=$(cat)

# Extract message (Claude passes JSON, we'll extract the message)
message=$(echo "$notification" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)

# If no message extracted, use the full notification
if [ -z "$message" ]; then
    message="Claude needs your attention!"
fi

# Send macOS notification with sound
osascript -e "display notification \"$message\" with title \"Claude Code\" sound name \"Glass\""

# Also speak the notification (optional - comment out if too intrusive)
# say "Claude needs your attention"