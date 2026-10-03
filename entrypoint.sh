#!/bin/bash
set -e

# Start virtual X server in background if not already running
if [ -z "$DISPLAY" ]; then
    export DISPLAY=:99
fi

if ! pgrep -x "Xvfb" > /dev/null; then
    Xvfb :99 -screen 0 1280x1024x24 -ac +extension GLX +render -noreset > /dev/null 2>&1 &
    for i in {1..10}; do
        if [ -e /tmp/.X11-unix/X99 ]; then
            break
        fi
        sleep 0.2
    done
fi

exec "$@"
