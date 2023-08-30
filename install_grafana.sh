# Install dependencies
sudo apt-get update
sudo apt-get install -y software-properties-common

# Add Grafana repository
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"

# Import GPG key
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -

# Install Grafana
sudo apt-get update
sudo apt-get install grafana

# Start Grafana service
# sudo systemctl start grafana-server

# Enable Grafana service to start on boot
# sudo systemctl enable grafana-server

# Grafana executable path
grafana_path=$(which grafana-server)
