#!/bin/bash

# Pergunta ao usuário para escolher entre prod ou dev
echo "Escolha o ambiente (1- dev, 2- local):"
read ambiente

export NGROK_URL="127.0.0.1"
sudo docker start grafana
sudo docker start tele-prometheus

# Verifica a escolha do usuário e exporta as configurações apropriadas
if [ $ambiente -eq 1 ]; then
    sudo docker start tele-redis
    python3 web_scrapper.py

elif [ $ambiente -eq 2 ]; then
    export MONGO_URL="mongodb://localhost"

    # Verifica o MongoDB
    if pgrep mongod > /dev/null; then
        echo "O MongoDB está em execução. Continuando..."
    else
        echo "O MongoDB não está em execução. Inicie o MongoDB e execute o script novamente."
        exit 1
    fi

    # Verifica o Redis
    if pgrep redis > /dev/null; then
        echo "O Redis está em execução. Continuando..."
    else
        echo "O Redis não está em execução. Inicie o Redis e execute o script novamente."
        exit 1
    fi

    python3 chat_bot.py

else
    echo "Opção inválida. Por favor, escolha 1 para prod ou 2 para dev."
    exit 1
fi
