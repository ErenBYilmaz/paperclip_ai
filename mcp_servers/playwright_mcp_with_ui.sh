#!/usr/bin/env -S bash -ex
export DISPLAY=host.docker.internal:0.0
Xvfb host.docker.internal:0.0 -screen 0 1280x800x24 -ac >/dev/null 2>&1 &
x11vnc -display host.docker.internal:0.0 -forever -rfbauth /home/myuser/.vncpass -listen 0.0.0.0 -rfbport 5900 >/dev/null 2>&1 &
sudo service dbus start
echo $DISPLAY
sleep 1
npx --no-install @executeautomation/playwright-mcp-server 3<&0 2>&1