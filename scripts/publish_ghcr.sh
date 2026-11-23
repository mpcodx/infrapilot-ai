#!/usr/bin/env bash
set -euo pipefail

# InfraPilot AI — GHCR Image Build & Push Script
# Usage:
#   export GITHUB_USERNAME="your-github-handle"
#   export GITHUB_TOKEN="ghp_yourpersonalaccesstoken"
#   ./scripts/publish_ghcr.sh [VERSION]

VERSION="${1:-1.0.0}"
GITHUB_USERNAME="${GITHUB_USERNAME:-}"

if [ -z "$GITHUB_USERNAME" ]; then
  echo "Error: GITHUB_USERNAME is required."
  echo "Usage: GITHUB_USERNAME=myuser ./scripts/publish_ghcr.sh 1.0.0"
  exit 1
fi

BACKEND_IMAGE="ghcr.io/${GITHUB_USERNAME}/infrapilot-ai-api:${VERSION}"
FRONTEND_IMAGE="ghcr.io/${GITHUB_USERNAME}/infrapilot-ai:${VERSION}"

echo "=== Building Backend Image: ${BACKEND_IMAGE} ==="
docker build -t "${BACKEND_IMAGE}" -f backend/Dockerfile .

echo "=== Building Frontend Image: ${FRONTEND_IMAGE} ==="
docker build -t "${FRONTEND_IMAGE}" -f frontend/Dockerfile .

echo "=== Tagging :latest ==="
docker tag "${BACKEND_IMAGE}" "ghcr.io/${GITHUB_USERNAME}/infrapilot-ai-api:latest"
docker tag "${FRONTEND_IMAGE}" "ghcr.io/${GITHUB_USERNAME}/infrapilot-ai:latest"

if [ -n "${GITHUB_TOKEN:-}" ]; then
  echo "=== Logging in to GHCR ==="
  echo "${GITHUB_TOKEN}" | docker login ghcr.io -u "${GITHUB_USERNAME}" --password-stdin

  echo "=== Pushing Images to GHCR ==="
  docker push "${BACKEND_IMAGE}"
  docker push "ghcr.io/${GITHUB_USERNAME}/infrapilot-ai-api:latest"
  docker push "${FRONTEND_IMAGE}"
  docker push "ghcr.io/${GITHUB_USERNAME}/infrapilot-ai:latest"
  echo "=== Push Complete! ==="
else
  echo "NOTE: GITHUB_TOKEN not set. Images built locally. Run docker push manually after logging in."
fi
