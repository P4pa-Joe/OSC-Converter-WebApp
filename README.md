# OSC-Converter-WebApp

A Django-based web application for routing and converting OSC (Open Sound Control) messages. This tool allows you to receive OSC messages on a configurable port, remap their addresses, and forward them to different destinations.

## Features

- Web-based interface for easy configuration
- Multiple configurations with independent OSC listeners
- Flexible dispatcher system to remap OSC addresses
- Real-time log monitoring per configuration
- Auto-start configurations on server boot
- Export/Import configurations as JSON
- Test dispatchers directly from the interface

## Tested Platforms

- Raspbian "Bookworm"
- Debian 13.3.0 amd64 "Trixie"

## Quick Installation (Recommended)

The installation script handles everything automatically:

```bash
chmod +x install.sh
sudo ./install.sh
```

This script will:
- Install system dependencies (Python 3, venv, pip)
- Create the installation directory (`/opt/osc-converter-webapp`)
- Set up a Python virtual environment
- Install Python dependencies
- Run database migrations
- Initialize default configuration
- Optionally install and configure the systemd service

## Manual Installation

If you prefer to install manually:

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialize the database

```bash
python manage.py makemigrations converter
python manage.py migrate
```

### 3. Initialize default data

```bash
python init_data.py
```

### 4. Run the development server

```bash
python manage.py runserver 0.0.0.0:8000
```

### 5. Access the web interface

Open your browser at: http://127.0.0.1:8000

## Service Management

After installation with the systemd service:

```bash
# Check service status
sudo systemctl status osc-converter-webapp

# Start the service
sudo systemctl start osc-converter-webapp

# Stop the service
sudo systemctl stop osc-converter-webapp

# Restart the service
sudo systemctl restart osc-converter-webapp

# View logs
sudo journalctl -u osc-converter-webapp -f
```

## Configuration

1. Create a new configuration with a name, listening IP and port
2. Add dispatchers to map input OSC addresses to output addresses
3. Configure destination IP and port for each dispatcher
4. Enable auto-start if you want the configuration to start automatically
5. Start the configuration using the play button

## Export/Import

- **Export all**: Download all configurations and dispatchers as a JSON file
- **Import**: Upload a JSON file to restore configurations
- **Export dispatchers**: Export only the dispatchers of a specific configuration
- **Import dispatchers**: Import dispatchers into an existing configuration
