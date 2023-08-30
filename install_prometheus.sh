# Download Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.30.3/prometheus-2.30.3.linux-amd64.tar.gz

# Extract the downloaded archive
tar xvfz prometheus-2.30.3.linux-amd64.tar.gz

# Navigate to the extracted directory
mv prometheus-2.30.3.linux-amd64 prom-amd64
cd prom-amd64

# Prometheus executable path
prometheus_path=$(pwd)/prometheus

# Prometheus configuration path
prometheus_config_path=$(pwd)/prometheus.yml
