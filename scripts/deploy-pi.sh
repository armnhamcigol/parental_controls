#!/bin/bash
# Deployment script for Parental Controls on Raspberry Pi
# Run this script on your Raspberry Pi to deploy the application

set -e  # Exit on any error

echo "🛡️ Deploying Parental Controls Dashboard to Raspberry Pi"
echo "============================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    print_warning "This script is designed for Raspberry Pi. Continuing anyway..."
fi

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run this script as root"
    exit 1
fi

# Update system packages
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    print_status "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    print_success "Docker installed successfully"
else
    print_success "Docker is already installed"
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    print_status "Installing Docker Compose..."
    sudo pip3 install docker-compose
    print_success "Docker Compose installed successfully"
else
    print_success "Docker Compose is already installed"
fi

# Create application directory
APP_DIR="/home/$USER/parental-controls"
print_status "Creating application directory: $APP_DIR"
mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Check if SSH keys exist for OPNSense
SSH_KEY="$HOME/.ssh/id_ed25519_opnsense"
if [ ! -f "$SSH_KEY" ]; then
    print_warning "OPNSense SSH key not found at $SSH_KEY"
    print_status "Creating placeholder SSH key directory..."
    mkdir -p "$HOME/.ssh"
    chmod 700 "$HOME/.ssh"
    print_warning "Please copy your OPNSense SSH keys to $HOME/.ssh/"
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p config logs logs/nginx

# Set proper permissions
chmod 755 config logs logs/nginx

# Check if deployment files exist in current directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found in current directory"
    print_status "Please copy all deployment files to $(pwd) first:"
    print_status "  - docker-compose.yml"
    print_status "  - Dockerfile"
    print_status "  - nginx.conf"
    print_status "  - src/ directory"
    print_status "  - package.json"
    exit 1
fi

# Stop any existing containers
print_status "Stopping any existing containers..."
docker-compose down --remove-orphans || true

# Build and start the application
print_status "Building and starting the application..."
docker-compose up --build -d

# Wait for services to be healthy
print_status "Waiting for services to start..."
sleep 10

# Check container status
print_status "Checking container status..."
docker-compose ps

# Test the application
print_status "Testing application health..."
if curl -f http://localhost:8443/health &> /dev/null; then
    print_success "Application is running and healthy!"
else
    print_error "Application health check failed"
    print_status "Container logs:"
    docker-compose logs --tail=20
    exit 1
fi

# Get Raspberry Pi IP address
PI_IP=$(hostname -I | awk '{print $1}')

# Display success information
echo ""
print_success "🎉 Deployment completed successfully!"
echo "=============================================="
print_status "Dashboard URL: http://$PI_IP:8443"
print_status "Health Check: http://$PI_IP:8443/health"
print_status "API Status: http://$PI_IP:8443/api/status"
echo ""
print_status "Quick commands:"
echo "  View logs:        docker-compose logs -f"
echo "  Restart:          docker-compose restart"
echo "  Update:           docker-compose pull && docker-compose up -d"
echo "  Stop:             docker-compose down"
echo ""

# Display container resource usage
print_status "Container resource usage:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.PIDs}}"

# Check available disk space
print_status "Available disk space:"
df -h / | tail -1

# Create systemd service for auto-start (optional)
read -p "Would you like to create a systemd service for auto-start on boot? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Creating systemd service..."
    
    sudo tee /etc/systemd/system/parental-controls.service > /dev/null <<EOF
[Unit]
Description=Parental Controls Dashboard
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0
User=$USER

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable parental-controls.service
    print_success "Systemd service created and enabled"
fi

echo ""
print_success "🛡️ Parental Controls Dashboard is now running on your Raspberry Pi!"
print_status "Access it at: http://$PI_IP:8443"
echo ""

# Show next steps
print_status "Next steps:"
echo "1. Configure API credentials for Nintendo, Google, and Microsoft"
echo "2. Set up SSH key access to your OPNSense firewall"
echo "3. Test the toggle functionality"
echo "4. Create child profiles as needed"
echo "5. Bookmark the dashboard URL on your devices"
echo ""
print_warning "Remember to secure your Raspberry Pi with proper firewall rules!"

exit 0
