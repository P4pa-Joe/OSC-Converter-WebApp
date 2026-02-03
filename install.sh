#!/bin/bash
#
# OSC Converter WebApp - Installation Script
# For Debian/Ubuntu systems
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  OSC Converter WebApp - Installation  ${NC}"
echo -e "${GREEN}========================================${NC}"
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Erreur: Ce script doit être exécuté avec sudo${NC}"
    echo -e "Usage: ${YELLOW}sudo ./install.sh${NC}"
    echo
    exit 1
fi

INSTALL_DIR="/opt/osc-converter-webapp"

# Install system dependencies
echo -e "${GREEN}[1/7] Installing system dependencies...${NC}"
apt-get update
apt-get install -y python3 python3-venv python3-pip

# Create installation directory
echo -e "${GREEN}[2/7] Creating installation directory...${NC}"
mkdir -p "$INSTALL_DIR"
cp -r . "$INSTALL_DIR/"
cd "$INSTALL_DIR"

# Create virtual environment
echo -e "${GREEN}[3/7] Creating Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "${GREEN}[4/7] Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Run Django migrations
echo -e "${GREEN}[5/7] Running database migrations...${NC}"
python manage.py makemigrations converter
python manage.py migrate

# Collect static files
echo -e "${GREEN}[6/7] Collecting static files...${NC}"
python manage.py collectstatic --noinput 2>/dev/null || true

# Initialize default data
echo -e "${GREEN}[7/7] Initializing default configuration...${NC}"
python init_data.py

# Ask to install systemd service
echo -e "${YELLOW}Do you want to install the systemd service? (y/n)${NC}"
read -r INSTALL_SERVICE

if [ "$INSTALL_SERVICE" = "y" ] || [ "$INSTALL_SERVICE" = "Y" ]; then
    echo -e "${GREEN}Installing systemd service...${NC}"

    # Update service file with correct path
    sed -i "s|WorkingDirectory=.*|WorkingDirectory=$INSTALL_DIR|g" osc-converter-webapp.service
    sed -i "s|ExecStart=.*|ExecStart=$INSTALL_DIR/venv/bin/gunicorn --bind 0.0.0.0:8000 --workers 1 osc_converter.wsgi:application|g" osc-converter-webapp.service

    # Fix permissions for www-data user (service runs as www-data)
    # SQLite needs write access to the directory for journal/WAL files
    sudo chown -R www-data:www-data "$INSTALL_DIR"

    sudo cp osc-converter-webapp.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable osc-converter-webapp

    echo -e "${YELLOW}Do you want to start the service now? (y/n)${NC}"
    read -r START_SERVICE

    if [ "$START_SERVICE" = "y" ] || [ "$START_SERVICE" = "Y" ]; then
        sudo systemctl start osc-converter-webapp
        echo -e "${GREEN}Service started!${NC}"
    fi

    echo
    echo -e "Service commands:"
    echo -e "  ${YELLOW}sudo systemctl status osc-converter-webapp${NC}  - Check status"
    echo -e "  ${YELLOW}sudo systemctl restart osc-converter-webapp${NC} - Restart"
    echo -e "  ${YELLOW}sudo systemctl stop osc-converter-webapp${NC}    - Stop"
else
    echo -e "To start the server manually:"
    echo -e "  ${YELLOW}cd $INSTALL_DIR${NC}"
    echo -e "  ${YELLOW}source venv/bin/activate${NC}"
    echo -e "  ${YELLOW}python manage.py runserver 0.0.0.0:8000${NC}"
fi

echo
echo -e "Access the web interface at: ${GREEN}http://localhost:8000${NC}"
echo -e "${GREEN}Installation complete!${NC}"
exit 0