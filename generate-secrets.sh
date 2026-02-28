#!/bin/bash
# Script to generate secret files for local development

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
echo "These files will be mounted to the container at /app/secrets/"
