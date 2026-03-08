#!/usr/bin/env bash
# EC2 initial setup script
# Run this ONCE on a fresh Ubuntu 22.04+ EC2 instance
# Usage: ssh ubuntu@<ec2-ip> 'bash -s' < deploy/setup-ec2.sh

set -euo pipefail

echo "=== Updating system ==="
sudo apt-get update && sudo apt-get upgrade -y

echo "=== Installing Docker ==="
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Allow current user to run Docker without sudo
sudo usermod -aG docker "$USER"

echo "=== Creating app directory ==="
sudo mkdir -p /opt/app
sudo chown "$USER:$USER" /opt/app

echo "=== Cloning repository ==="
echo "NOTE: You need to set up a deploy key or personal access token for git clone."
echo "Run: cd /opt/app && git clone <your-repo-url> ."

echo ""
echo "=== Setup complete ==="
echo "Next steps:"
echo "  1. Log out and back in (for Docker group to take effect)"
echo "  2. cd /opt/app && git clone <your-repo-url> ."
echo "  3. cp .env.production.example .env.production"
echo "  4. Edit .env.production with real credentials"
echo "  5. docker compose -f docker-compose.prod.yml --profile migration run --rm migrate"
echo "  6. docker compose -f docker-compose.prod.yml up -d"
