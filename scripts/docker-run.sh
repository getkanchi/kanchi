#!/bin/bash

# Helper script to run Kanchi Docker container with proper networking

set -e

# Default values
IMAGE_NAME="${IMAGE_NAME:-kanchi:latest}"
RABBITMQ_HOST="${RABBITMQ_HOST:-localhost}"
RABBITMQ_PORT="${RABBITMQ_PORT:-5672}"
RABBITMQ_USER="${RABBITMQ_USER:-guest}"
RABBITMQ_PASS="${RABBITMQ_PASS:-guest}"
RABBITMQ_VHOST="${RABBITMQ_VHOST:-/}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"
WS_PORT="${WS_PORT:-8765}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
WS_PUBLIC_HOST="${WS_PUBLIC_HOST:-localhost}"

# Function to detect platform and adjust localhost
detect_docker_host() {
    if [ "$RABBITMQ_HOST" = "localhost" ] || [ "$RABBITMQ_HOST" = "127.0.0.1" ]; then
        case "$(uname -s)" in
            Darwin|MINGW*|MSYS*|CYGWIN*)
                # macOS and Windows
                echo "host.docker.internal"
                ;;
            Linux)
                # Linux - try to get docker0 bridge IP
                if command -v ip &> /dev/null; then
                    docker0_ip=$(ip -4 addr show docker0 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1)
                    if [ -n "$docker0_ip" ]; then
                        echo "$docker0_ip"
                    else
                        echo "172.17.0.1"  # Default Docker bridge gateway
                    fi
                else
                    echo "172.17.0.1"  # Default Docker bridge gateway
                fi
                ;;
            *)
                echo "$RABBITMQ_HOST"
                ;;
        esac
    else
        echo "$RABBITMQ_HOST"
    fi
}

# Function to test RabbitMQ connectivity
test_rabbitmq() {
    local host=$1
    local port=$2
    
    echo "Testing connection to RabbitMQ at $host:$port..."
    
    if command -v nc &> /dev/null; then
        if nc -zv -w5 "$host" "$port" 2>&1 | grep -q "succeeded\|open"; then
            echo "✓ RabbitMQ is reachable at $host:$port"
            return 0
        else
            echo "✗ Cannot connect to RabbitMQ at $host:$port"
            return 1
        fi
    elif command -v telnet &> /dev/null; then
        if timeout 5 bash -c "echo > /dev/tcp/$host/$port" 2>/dev/null; then
            echo "✓ RabbitMQ is reachable at $host:$port"
            return 0
        else
            echo "✗ Cannot connect to RabbitMQ at $host:$port"
            return 1
        fi
    else
        echo "⚠ Cannot test connection (nc or telnet not available)"
        return 0
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --rabbitmq-host)
            RABBITMQ_HOST="$2"
            shift 2
            ;;
        --rabbitmq-port)
            RABBITMQ_PORT="$2"
            shift 2
            ;;
        --rabbitmq-user)
            RABBITMQ_USER="$2"
            shift 2
            ;;
        --rabbitmq-pass)
            RABBITMQ_PASS="$2"
            shift 2
            ;;
        --rabbitmq-vhost)
            RABBITMQ_VHOST="$2"
            shift 2
            ;;
        --log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        --image)
            IMAGE_NAME="$2"
            shift 2
            ;;
        --ws-port)
            WS_PORT="$2"
            shift 2
            ;;
        --frontend-port)
            FRONTEND_PORT="$2"
            shift 2
            ;;
        --ws-public-host)
            WS_PUBLIC_HOST="$2"
            shift 2
            ;;
        --help)
            cat << EOF
Usage: $0 [OPTIONS]

Run Kanchi Docker container with proper networking configuration.

Options:
    --rabbitmq-host HOST    RabbitMQ host (default: localhost, auto-detected for Docker)
    --rabbitmq-port PORT    RabbitMQ port (default: 5672)
    --rabbitmq-user USER    RabbitMQ username (default: guest)
    --rabbitmq-pass PASS    RabbitMQ password (default: guest)
    --rabbitmq-vhost VHOST  RabbitMQ virtual host (default: /)
    --log-level LEVEL       Log level (default: INFO)
    --image NAME            Docker image name (default: kanchi:latest)
    --ws-port PORT          WebSocket port (default: 8765)
    --frontend-port PORT    Frontend port (default: 3000)
    --ws-public-host HOST   Public hostname/IP for WebSocket (default: localhost, use EC2 public IP for EC2)
    --help                  Show this help message

Examples:
    # Connect to RabbitMQ on host machine (auto-detected)
    $0

    # Connect to RabbitMQ on another server
    $0 --rabbitmq-host rabbitmq.example.com

    # Connect to RabbitMQ on EC2 instance with public WebSocket access
    $0 --rabbitmq-host 10.0.1.23 --rabbitmq-user myuser --rabbitmq-pass mypass --ws-public-host ec2-52-12-34-56.compute-1.amazonaws.com

    # Run with debug logging
    $0 --log-level DEBUG
EOF
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Detect the correct Docker host for localhost connections
ACTUAL_HOST=$(detect_docker_host)

# URL encode the vhost
ENCODED_VHOST=$(printf '%s' "$RABBITMQ_VHOST" | sed 's|/|%2F|g')

# Construct the AMQP URL
CELERY_BROKER_URL="amqp://${RABBITMQ_USER}:${RABBITMQ_PASS}@${ACTUAL_HOST}:${RABBITMQ_PORT}/${ENCODED_VHOST}"

# Construct the WebSocket URL for the frontend
WS_URL="ws://${WS_PUBLIC_HOST}:${WS_PORT}/ws"

echo "========================================="
echo "Kanchi Docker Container Configuration"
echo "========================================="
echo "Image:        $IMAGE_NAME"
echo "Broker URL:   $CELERY_BROKER_URL"
echo "WebSocket:    http://localhost:$WS_PORT (internal)"
echo "              $WS_URL (public)"
echo "Frontend:     http://localhost:$FRONTEND_PORT"
echo "Log Level:    $LOG_LEVEL"
echo "========================================="

# Test RabbitMQ connectivity from host
if [ "$RABBITMQ_HOST" = "localhost" ] || [ "$RABBITMQ_HOST" = "127.0.0.1" ]; then
    test_rabbitmq "localhost" "$RABBITMQ_PORT"
else
    test_rabbitmq "$RABBITMQ_HOST" "$RABBITMQ_PORT"
fi

echo ""
echo "Starting container..."
echo ""

# Run the Docker container
docker run \
    --name kanchi-monitor \
    --rm \
    -it \
    -p "${WS_PORT}:8765" \
    -p "${FRONTEND_PORT}:3000" \
    -e "CELERY_BROKER_URL=${CELERY_BROKER_URL}" \
    -e "LOG_LEVEL=${LOG_LEVEL}" \
    -e "NUXT_PUBLIC_WS_URL=${WS_URL}" \
    "$IMAGE_NAME"