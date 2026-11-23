# Publishing InfraPilot AI to GitHub Container Registry (GHCR)

This guide documents how to build, tag, and publish the InfraPilot AI images to GitHub Container Registry so they can be referenced in SoloHost packages.

## 1. Prerequisites

- A GitHub account.
- A GitHub Personal Access Token (PAT) with `write:packages`, `read:packages`, and `repo` scopes.

## 2. Docker Authentication

Log in to GitHub Container Registry:

```bash
export CR_PAT="YOUR_PERSONAL_ACCESS_TOKEN"
echo $CR_PAT | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

## 3. Automated Build and Publishing

Use the provided build script:

```bash
export GITHUB_USERNAME="your-github-username"
export GITHUB_TOKEN="$CR_PAT"
./scripts/publish_ghcr.sh 1.0.0
```

## 4. Making Packages Public

By default, newly pushed packages on GHCR may be private:
1. Navigate to your GitHub profile -> **Packages**.
2. Select `infrapilot-ai` and `infrapilot-ai-api`.
3. Click **Package settings** -> **Danger Zone** -> **Change package visibility**.
4. Set visibility to **Public** so SoloHost nodes can pull the images.

## 5. SoloHost Package Integration

Update `deployment/solohost/docker-compose.yml` with your public image name:

```yaml
services:
  backend:
    image: ghcr.io/YOUR_GITHUB_USERNAME/infrapilot-ai-api:1.0.0
  web:
    image: ghcr.io/YOUR_GITHUB_USERNAME/infrapilot-ai:1.0.0
```
