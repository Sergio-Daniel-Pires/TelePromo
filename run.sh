#!/bin/bash

echo "Running local web scrapper and chat bot"

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

# Executa os scripts Python em background
python3 chat_bot.py &
CHAT_BOT_PID=$!
python3 web_scrapper.py &
WEB_SCRAPPER_PID=$!

# Define uma função para terminar ambos os processos
cleanup() {
    echo "Terminating both processes..."
    kill $CHAT_BOT_PID $WEB_SCRAPPER_PID
}

# Captura os sinais de saída para limpeza
trap cleanup EXIT SIGINT SIGTERM

# Espera ambos os processos terminarem
wait $CHAT_BOT_PID $WEB_SCRAPPER_PID
