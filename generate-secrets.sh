#!/bin/bash
# Script to generate test secrets for Docker Secrets usage

mkdir -p ./secrets

# Generate credentials
USERNAME="apiuser"
PASSWORD="securepassword123"

# Create secret files
echo "$USERNAME" > ./secrets/api_username
echo "$PASSWORD" > ./secrets/api_password

# Set proper permissions (read-only)
chmod 400 ./secrets/api_username
chmod 400 ./secrets/api_password

echo "✓ Secrets generated in ./secrets/ directory"
echo "  Username: $USERNAME"
echo "  Password: (from ./secrets/api_password)"
echo ""
echo "For Docker Swarm, use: docker secret create"
echo "  docker secret create api_username ./secrets/api_username"
echo "  docker secret create api_password ./secrets/api_password"
