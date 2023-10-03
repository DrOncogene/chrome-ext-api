#!/bin/bash

app_dir="/app/chrome_ext_api"

# Path to the Nginx configuration file
nginx_config_file_name="chrome_ext_api.conf"
nginx_config="/etc/nginx/sites-available/$nginx_config_file_name"

# Configuration to add
sudo printf %s "server {
    listen 80;
    listen [::]:80 default_server;
    root /var/www/html;
    index index.html;
    server_name crome-ext-api.droncogene.com;
#    server_name 35.193.20.212;
    location = /recording_12 {
        return 301 https://clipchamp.com/watch/XPvIgZnx6Sg;
    }
    location ~ / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
#    location / {
#        try_files \$uri \$uri/ =404;
#    }
}" | sudo tee "$nginx_config" > /dev/null

# Remove any configuration file present
sudo rm "/etc/nginx/sites-enabled/$nginx_config_file_name"
# Create a symlink to the new configuration file
sudo ln -s "$nginx_config" /etc/nginx/sites-enabled/
# Navigate to the FastAPI application directory
cd "$app_dir" || exit
# Create a virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
# Activate the virtual environment
source .venv/bin/activate
# Install requirements
pip3 install -r requirements.txt
echo "Application setup complete"
# Check for syntax errors
sudo nginx -t
# Restart nginx
sudo systemctl reload nginx
sudo service nginx restart


# Replace these variables with your specific values
APP_NAME="chrome_ext_api"
USER="mypythtesting"
APP_DIRECTORY="/app/chrome_ext_api"
VENV_PATH="/app/chrome_ext_api/.venv"
UVICORN_OPTIONS="--host 0.0.0.0 --port 8001"
# Create a systemd service unit file
echo "[Unit]
Description=Backend API for Chrome Extension
[Service]
User=$USER
WorkingDirectory=$APP_DIRECTORY
ExecStart=$VENV_PATH/bin/uvicorn main:app $UVICORN_OPTIONS
Restart=always
[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/$APP_NAME.service > /dev/null
# Reload systemd
sudo systemctl daemon-reload
#stop the service
sudo systemctl stop $APP_NAME
# Start and enable the service
sudo systemctl start $APP_NAME
sudo systemctl enable $APP_NAME
# Check the status of the service
sudo systemctl status $APP_NAME

# start mongodb with docker
sudo docker start mongodb
