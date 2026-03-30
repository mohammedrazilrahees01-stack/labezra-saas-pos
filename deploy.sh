#!/bin/bash
# Labezra POS — Hostinger VPS Deployment Script
# Run this on your VPS after uploading the project

set -e

echo "🚀 Labezra POS — Deployment Starting..."

# Install system dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx supervisor

# Create project directory
sudo mkdir -p /var/www/labezra
sudo chown $USER:$USER /var/www/labezra

# Copy project files (run from project root)
cp -r . /var/www/labezra/

cd /var/www/labezra

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install django gunicorn pillow python-dotenv whitenoise

# Copy environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Please edit /var/www/labezra/.env with your settings!"
fi

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Edit /var/www/labezra/.env with your settings"
echo "2. Configure Nginx (see nginx.conf)"
echo "3. Set up Supervisor for Gunicorn"
echo "4. Run: sudo supervisorctl reload"
echo ""
