#!/bin/bash

required_commands=("grafana-server" "mongod")

export VENV_PATH="$(pipenv --venv)"
export GRAFANA_PATH="$(which grafana-server)"
export PROMETHEUS_PATH="$(pwd)/prom-amd64"
export PROJECT_PARENT="$(pwd)"
export PROJECT_PATH="$(pwd)/project"

# Function to stop Prometheus when the script exits
function finish {
    echo "Stopping Prometheus..."
    pkill -f prometheus
    echo "Stopping MongoDB..."
    pkill -f mongod
}

# Set up the trap to call the finish function on script exit
trap finish EXIT

for cmd in "${required_commands[@]}"; do
    if ! which "$cmd" >/dev/null; then
        echo "$cmd not found, exiting..."
        exit 1
    fi
done

if [ ! -d "$PROMETHEUS_PATH" ]; then
    echo "prometheus path not found"
    exit 1
fi

if [ ! -d "logs/" ]; then
    mkdir logs/
fi

cp "$PROJECT_PARENT/prometheus_dev.yml" "$PROMETHEUS_PATH/prometheus.yml"

"$PROJECT_PARENT/prom-amd64/prometheus" &
sudo /usr/bin/mongod --bind_ip_all --dbpath "$PROJECT_PARENT/db"
sudo systemctl start grafana-server

"$VENV_PATH/bin/python3" app.py