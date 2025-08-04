#!/bin/bash

# Stockholm Bus App - Nginx Setup Script
set -e

echo "Setting up Stockholm Bus App with Nginx..."

# Variables
APP_DIR="/home/ubuntu/bus_app"
APP_USER="ubuntu"
DOMAIN="your-domain.com"

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "Installing Nginx and other dependencies..."
sudo apt install -y nginx python3 python3-pip python3-venv git certbot python3-certbot-nginx

# Create application directory
echo "Setting up application directory..."
sudo mkdir -p $APP_DIR
sudo chown $APP_USER:$APP_USER $APP_DIR

# Setup Python virtual environment
echo "Creating Python virtual environment..."
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy systemd service files
echo "Setting up systemd services..."
sudo cp systemd/gunicorn.service /etc/systemd/system/
sudo cp systemd/gunicorn.socket /etc/systemd/system/

# Copy Nginx configuration
echo "Setting up Nginx configuration..."
sudo cp nginx/sites-available/bus-app /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/bus-app /etc/nginx/sites-enabled/

# Remove default Nginx site
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
echo "Testing Nginx configuration..."
sudo nginx -t

# Enable and start services
echo "Enabling and starting services..."
sudo systemctl daemon-reload
sudo systemctl enable gunicorn.socket
sudo systemctl start gunicorn.socket
sudo systemctl enable nginx
sudo systemctl restart nginx

# Setup SSL with Let's Encrypt (optional)
echo "Do you want to setup SSL with Let's Encrypt? (y/n)"
read -r ssl_setup
if [[ $ssl_setup == "y" || $ssl_setup == "Y" ]]; then
    echo "Setting up SSL certificate..."
    sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN
fi

# Set up firewall
echo "Configuring firewall..."
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw --force enable

echo "Setup complete!"
echo "Your Stockholm Bus App should now be available at:"
echo "HTTP: http://$DOMAIN"
echo "HTTPS: https://$DOMAIN (if SSL was configured)"
echo ""
echo "Useful commands:"
echo "- Check Gunicorn status: sudo systemctl status gunicorn"
echo "- Check Nginx status: sudo systemctl status nginx"
echo "- View Nginx logs: sudo tail -f /var/log/nginx/error.log"
echo "- Restart application: sudo systemctl restart gunicorn"
