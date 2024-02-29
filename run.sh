#!/bin/bash

echo "Running local web scrapper"

# Exports
export REDIS_URL="127.0.0.1"
export NGROK_URL="127.0.0.1"
export MONGO_CONN_STR="mongodb://127.0.0.1:27017/"

# Verifica o Redis
if pgrep redis > /dev/null; then
    echo "Stopping local redis to start from container"
    sudo systemctl stop redis
fi

# Start docker
sudo docker start tele-redis
sudo docker start grafana
sudo docker start tele-prometheus

# Verifica o MongoDB
if pgrep mongod > /dev/null; then
    echo "MongoDB Ok"
else
    echo "MongoDB aren't running. Please, start MongoDB and try again"
    exit 1
fi

python3 chat_bot.py
