#!/bin/bash

# Update system packages
sudo apt update -y

# Install Apache to simulate a web server running on the instance
sudo apt install -y apache2

# Start Apache service
sudo systemctl start apache2

# Install and configure UFW (Uncomplicated Firewall)
sudo apt install -y ufw

# Allow SSH (port 22) and HTTP (port 80)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp

# Deny all other incoming traffic by default
sudo ufw default deny incoming

# Enable the firewall
sudo ufw --force enable

# Print the status of UFW for confirmation
sudo ufw status verbose