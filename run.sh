#!/bin/bash

# Pergunta ao usuário para escolher entre prod ou dev
echo "Escolha o ambiente (1- dev, 2- local):"
read ambiente

export TELEGRAM_TOKEN="6649989525:AAHgeYTN-x7jjZy2GHAxaCXBSwz-w6e_87c"
sudo docker start tele-redis
sudo docker start grafana
sudo docker start tele_prometheus

# Verifica a escolha do usuário e exporta as configurações apropriadas
if [ $ambiente -eq 1 ]; then
    export MONGO_URL="mongodb+srv://gaosan:Ws0IX3kripgqWKDW@telepromo.sgqmifa.mongodb.net/"

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

else
    echo "Opção inválida. Por favor, escolha 1 para prod ou 2 para dev."
    exit 1
fi
