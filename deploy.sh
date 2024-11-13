#!/bin/bash

# Set strict error handling
set -euo pipefail
trap 'echo "Error on line $LINENO"' ERR

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values for flags
CLEANUP_ONLY=false
NO_CACHE=false
SKIP_HEALTH_CHECK=false
FORCE_CERTS=false
FORCE_OQS=false
RUN_TESTS=false
VERBOSE=false

# Function to display usage information
usage() {
    echo -e "${BLUE}Usage:${NC} $0 [options]"
    echo
    echo "Options:"
    echo "  --cleanup         Clean up old containers, images, and volumes only"
    echo "  --no-cache       Build images without using cache"
    echo "  --no-health      Skip health checks"
    echo "  --force-certs    Force recreation of certificates"
    echo "  --force-oqs      Force reinstallation of OQS libraries"
    echo "  --run-tests      Run test suite before deployment"
    echo "  --verbose        Show more detailed output"
    echo "  --help           Show this help message"
    echo
    exit 1
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --cleanup)
                CLEANUP_ONLY=true
                shift
                ;;
            --no-cache)
                NO_CACHE=true
                shift
                ;;
            --no-health)
                SKIP_HEALTH_CHECK=true
                shift
                ;;
            --force-certs)
                FORCE_CERTS=true
                shift
                ;;
            --force-oqs)
                FORCE_OQS=true
                shift
                ;;
            --run-tests)
                RUN_TESTS=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                usage
                ;;
            *)
                error "Unknown option: $1"
                usage
                ;;
        esac
    done
}

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

verbose() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] VERBOSE:${NC} $1"
    fi
}

# Install system dependencies for OQS
install_oqs_dependencies() {
    log "Installing liboqs dependencies..."

    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        sudo apt-get update
        sudo apt-get install -y \
            astyle \
            cmake \
            gcc \
            ninja-build \
            libssl-dev \
            python3-pytest \
            python3-pytest-xdist \
            unzip \
            xsltproc \
            doxygen \
            graphviz \
            python3-yaml \
            valgrind \
            python3-pip \
            build-essential \
            git
    elif command -v brew &> /dev/null; then
        # macOS
        brew install \
            cmake \
            ninja \
            openssl@3 \
            astyle \
            python3 \
            doxygen \
            graphviz
    else
        error "Unsupported package manager. Please install dependencies manually."
        exit 1
    fi

    verbose "Dependencies installed successfully"
}

# Install and build liboqs
install_liboqs() {
    log "Installing liboqs..."

    LIBOQS_DIR="liboqs"
    if [ -d "$LIBOQS_DIR" ]; then
        verbose "Updating existing liboqs..."
        cd "$LIBOQS_DIR"
        git pull
    else
        verbose "Cloning liboqs..."
        git clone --recurse-submodules https://github.com/open-quantum-safe/liboqs.git
        cd "$LIBOQS_DIR"
    fi

    verbose "Building liboqs..."
    mkdir -p build && cd build
    cmake -GNinja -DCMAKE_INSTALL_PREFIX=/usr/local ..
    ninja
    sudo ninja install

    cd ../..
    verbose "liboqs installed successfully"
}

# Install python-oqs
install_python_oqs() {
    log "Installing python-oqs..."

    PYTHON_OQS_DIR="python-oqs"
    if [ -d "$PYTHON_OQS_DIR" ]; then
        verbose "Updating existing python-oqs..."
        cd "$PYTHON_OQS_DIR"
        git pull
    else
        verbose "Cloning python-oqs..."
        git clone https://github.com/open-quantum-safe/python-oqs.git
        cd "$PYTHON_OQS_DIR"
    fi

    verbose "Building and installing python-oqs..."
    python3 setup.py build
    sudo python3 setup.py install

    cd ..
    verbose "python-oqs installed successfully"
}

# Check if Docker is installed and running
check_docker() {
    log "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        error "Docker daemon is not running. Please start Docker."
        exit 1
    fi

    verbose "Docker version: $(docker --version)"
    log "Docker is running properly"
}

# Check if Docker Compose is installed
check_docker_compose() {
    log "Checking Docker Compose installation..."
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    verbose "Docker Compose version: $(docker-compose --version)"
    log "Docker Compose is installed"
}

# Check OQS installation
check_oqs_installation() {
    log "Checking OQS installation..."

    if [ "$FORCE_OQS" = true ]; then
        warn "Forcing OQS reinstallation..."
        install_oqs_dependencies
        install_liboqs
        install_python_oqs
        return
        fi


    # Check for liboqs
    if [ ! -f "/usr/local/lib/liboqs.so" ]; then
        warn "liboqs not found, will install..."
        install_oqs_dependencies
        install_liboqs
    else
        verbose "liboqs is installed"
    fi

    # Check for python-oqs
    if ! python3 -c "import oqs" &> /dev/null; then
        warn "python-oqs not found, will install..."
        install_python_oqs
    else
        verbose "python-oqs is installed"
    fi
}

# Run test suite
run_tests() {
    log "Running test suite..."

    # Create test container
    docker-compose -f docker-compose.yml -f docker-compose.test.yml up \
        --build --abort-on-container-exit test

    # Check test exit code
    if [ $? -ne 0 ]; then
        error "Tests failed!"
        exit 1
    fi

    log "Tests passed successfully"
}

# Setup directories
setup_directories() {
    log "Setting up directory structure..."

    directories=(
        "vault/config"
        "vault/logs"
        "vault/file"
        "nats/config"
        "prometheus"
        "grafana/provisioning/dashboards"
        "grafana/provisioning/datasources"
        "secrets"
        "certs"
    )

    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            verbose "Creating directory: $dir"
            mkdir -p "$dir"
        fi
    done
}

# Setup configurations
setup_configs() {
    log "Setting up configuration files..."

    # Check and create .env file
    if [ ! -f ".env" ]; then
        log "Creating .env file..."
        cat > .env << EOL
GRAFANA_ADMIN_PASSWORD=admin
NATS_AUTH_TOKEN=$(openssl rand -base64 32)
VAULT_DEV_ROOT_TOKEN_ID=$(openssl rand -base64 32)
EOL
        log "Created .env file with secure random tokens"
    else
        warn ".env file already exists. Skipping..."
    fi

    # Setup Vault config
    if [ ! -f "vault/config/vault.json" ]; then
        verbose "Creating Vault configuration..."
        cat > vault/config/vault.json << EOL
{
  "backend": {
    "file": {
      "path": "/vault/data"
    }
  },
  "listener": {
    "tcp": {
      "address": "0.0.0.0:8200",
      "tls_disable": 1
    }
  },
  "ui": true,
  "disable_mlock": true,
  "api_addr": "http://0.0.0.0:8200",
  "cluster_addr": "https://0.0.0.0:8201",
  "storage": {
    "file": {
      "path": "/vault/file"
    }
  }
}
EOL
    fi

    # Setup NATS config
    if [ ! -f "nats/config/nats.conf" ]; then
        verbose "Creating NATS configuration..."
        cat > nats/config/nats.conf << EOL
jetstream {
    store_dir: "/data"
    max_memory_store: 8GB
    max_file_store: 10GB
}

authorization {
    token: "\$NATS_AUTH_TOKEN"
}

http_port: 8222
monitor_port: 8222
http_port: localhost:8222

debug: false
trace: false
EOL
    fi
}

# Set permissions
set_permissions() {
    log "Setting correct permissions..."

    chmod -R 755 vault/
    chmod -R 755 nats/
    chmod 600 .env

    if [ -d "secrets" ]; then
        chmod 700 secrets/
        chmod 600 secrets/*
    fi

    verbose "Permissions set successfully"
}

# Generate certificates
generate_certs() {
    if [ "$FORCE_CERTS" = true ] || [ ! -f "certs/cert.pem" ] || [ ! -f "certs/key.pem" ]; then
        log "Generating self-signed certificates..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout certs/key.pem \
            -out certs/cert.pem \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    else
        verbose "Certificates exist, skipping generation"
    fi
}

# Update Dockerfile with OQS
update_dockerfile_oqs() {
    log "Updating Dockerfile with OQS dependencies..."
    # Copy the Dockerfile content from earlier
    # [Previous Dockerfile content with OQS...]
}

# Clean up resources
cleanup() {
    log "Cleaning up resources..."

    docker-compose down -v
    docker image prune -f
    docker volume prune -f

    verbose "Cleanup completed"
}

# Build and deploy
deploy() {
   log "Building and deploying services..."

    log "Building oqs-builder image..."
    docker-compose build oqs-builder

    build_cmd="docker-compose build api"
    if [ "$NO_CACHE" = true ]; then
        build_cmd="$build_cmd --no-cache"
        verbose "Building without cache"
    fi

    eval $build_cmd
    docker-compose up -d

    log "Waiting for services to start..."
    sleep 10
}

# Health checks
check_health() {
    if [ "$SKIP_HEALTH_CHECK" = true ]; then
        warn "Skipping health checks..."
        return
    fi

    log "Performing health checks..."

    services=("vault" "api" "nats" "prometheus" "grafana")

    for service in "${services[@]}"; do
        if docker-compose ps "$service" | grep -q "Up"; then
            log "$service is running"

            # Additional service-specific health checks
            case $service in
                "api")
                    curl -f http://localhost:8000/health &>/dev/null && \
                        log "API health check passed" || \
                        error "API health check failed"
                    ;;
                "vault")
                    curl -f http://localhost:8200/v1/sys/health &>/dev/null && \
                        log "Vault health check passed" || \
                        error "Vault health check failed"
                    ;;
            esac
        else
            error "$service is not running properly"
        fi
    done
}

# Setup OQS
setup_oqs() {
    if [ "$CLEANUP_ONLY" = false ]; then
        check_oqs_installation
        update_dockerfile_oqs
    fi
}

# Main deployment process
main() {
    log "Starting deployment process..."

    if [ "$CLEANUP_ONLY" = true ]; then
        cleanup
        exit 0
    fi

    # Check prerequisites
    check_docker
    check_docker_compose

    # Setup OQS
    #setup_oqs uncomment to setup libOQS

    # Run tests if requested
    if [ "$RUN_TESTS" = true ]; then
        run_tests
    fi

    # Setup
    setup_directories
    setup_configs
    set_permissions
    generate_certs

    # Deploy
    deploy

    # Post-deploy
    check_health

    if [ "$VERBOSE" = true ]; then
        docker-compose ps
        docker-compose logs
    fi

    log "Deployment completed successfully!"
    log "Access services at:"
    log "- API: http://localhost:8000"
    log "- Vault UI: http://localhost:8200"
    log "- Grafana: http://localhost:3000"
    log "- Prometheus: http://localhost:9090"
    log "- NATS Monitoring: http://localhost:8222"
}

# Parse command line arguments
parse_args "$@"

# Execute main function
main