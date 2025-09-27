#!/bin/bash

# 浮生十梦 Docker Deployment Script
# This script helps deploy the application using Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Global variable for Docker Compose command
DOCKER_COMPOSE_CMD=""

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check for Docker Compose (try both new and old commands)
    if docker compose version &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker compose"
    elif command_exists docker-compose; then
        DOCKER_COMPOSE_CMD="docker-compose"
    else
        print_error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    fi
    
    print_success "Prerequisites check passed."
}

# Setup environment file
setup_environment() {
    if [ ! -f .env ]; then
        print_status "Setting up environment file..."
        cp .env.docker.example .env
        print_warning "Please edit .env file with your configuration before continuing."
        print_warning "At minimum, you need to set:"
        print_warning "  - OPENAI_API_KEY"
        print_warning "  - SECRET_KEY (generate with: openssl rand -hex 32)"
        print_warning "  - AUTH_USERS (username:password pairs)"
        echo
        read -p "Press Enter after you've configured .env file..."
    else
        print_status "Environment file already exists."
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p data logs nginx/ssl
    print_success "Directories created."
}

# Generate SSL certificates (self-signed for development)
generate_ssl_certs() {
    if [ "$1" = "--ssl" ] && [ ! -f nginx/ssl/cert.pem ]; then
        print_status "Generating self-signed SSL certificates..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/key.pem \
            -out nginx/ssl/cert.pem \
            -subj "/C=CN/ST=State/L=City/O=Organization/CN=localhost"
        print_success "SSL certificates generated."
    fi
}

# Build and start services
deploy() {
    local profile=""
    if [ "$1" = "--with-nginx" ]; then
        profile="--profile nginx"
        print_status "Deploying with Nginx reverse proxy..."
    else
        print_status "Deploying application only..."
    fi
    
    print_status "Building Docker images..."
    $DOCKER_COMPOSE_CMD build

    print_status "Starting services..."
    $DOCKER_COMPOSE_CMD $profile up -d

    print_success "Deployment completed!"

    # Show status
    $DOCKER_COMPOSE_CMD ps
    
    echo
    print_success "Application is now running!"
    if [ "$1" = "--with-nginx" ]; then
        print_status "Access the application at: http://localhost"
        if [ -f nginx/ssl/cert.pem ]; then
            print_status "HTTPS access: https://localhost"
        fi
    else
        print_status "Access the application at: http://localhost:8000"
    fi
}

# Stop services
stop() {
    print_status "Stopping services..."
    $DOCKER_COMPOSE_CMD down
    print_success "Services stopped."
}

# Show logs
logs() {
    $DOCKER_COMPOSE_CMD logs -f
}

# Backup data
backup() {
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    print_status "Creating backup in $backup_dir..."
    mkdir -p "$backup_dir"
    cp -r data "$backup_dir/"
    cp .env "$backup_dir/"
    print_success "Backup created in $backup_dir"
}

# Update application
update() {
    print_status "Updating application..."
    $DOCKER_COMPOSE_CMD down
    $DOCKER_COMPOSE_CMD build --no-cache
    $DOCKER_COMPOSE_CMD up -d
    print_success "Application updated."
}

# Show help
show_help() {
    echo "浮生十梦 Docker Deployment Script"
    echo
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo
    echo "Commands:"
    echo "  deploy [--with-nginx] [--ssl]  Deploy the application"
    echo "  stop                           Stop all services"
    echo "  restart                        Restart all services"
    echo "  logs                           Show application logs"
    echo "  backup                         Create a backup of data"
    echo "  update                         Update and restart application"
    echo "  status                         Show service status"
    echo "  help                           Show this help message"
    echo
    echo "Options:"
    echo "  --with-nginx                   Deploy with Nginx reverse proxy"
    echo "  --ssl                          Generate self-signed SSL certificates"
    echo
    echo "Examples:"
    echo "  $0 deploy                      Deploy application only"
    echo "  $0 deploy --with-nginx         Deploy with Nginx"
    echo "  $0 deploy --with-nginx --ssl   Deploy with Nginx and SSL"
}

# Main script logic
case "$1" in
    deploy)
        check_prerequisites
        setup_environment
        create_directories
        generate_ssl_certs "$2"
        deploy "$2"
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        deploy
        ;;
    logs)
        logs
        ;;
    backup)
        backup
        ;;
    update)
        update
        ;;
    status)
        $DOCKER_COMPOSE_CMD ps
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo
        show_help
        exit 1
        ;;
esac
