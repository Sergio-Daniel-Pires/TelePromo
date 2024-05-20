#!/bin/bash

echo "Running local web scrapper and chat bot"

# Exports
export REDIS_URL="127.0.0.1"
export NGROK_URL="127.0.0.1"
export MONGO_CONN_STR="mongodb://127.0.0.1:27017/"

# Verifica o Redis
if pgrep redis > /dev/null; then
    echo "Redis Ok"
else
    echo "Redis aren't running. Please, start Redis and try again"
    exit 1
fi

# Start docker
sudo docker start grafana
sudo docker start tele-prometheus

# Verifica o MongoDB
if pgrep mongod > /dev/null; then
    echo "MongoDB Ok"
else
    echo "MongoDB aren't running. Please, start MongoDB and try again"
    exit 1
fi

# Executa os scripts Python em background
python3 chat_bot.py &
CHAT_BOT_PID=$!
python3 web_scrapper.py &
WEB_SCRAPPER_PID=$!

# Function to kill both processes
cleanup() {
    echo "Terminating both processes..."
    kill $CHAT_BOT_PID $WEB_SCRAPPER_PID
}

# Trap function to CTRL + C
trap cleanup EXIT SIGINT SIGTERM

wait $CHAT_BOT_PID $WEB_SCRAPPER_PID
