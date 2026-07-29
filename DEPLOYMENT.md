# Deployment

## VPS Requirements

- Ubuntu 24.04
- 2 CPU cores
- 4GB RAM

## Install Docker

1. Update package index:
   ```bash
   sudo apt update
   ```
2. Install prerequisites:
   ```bash
   sudo apt install -y ca-certificates curl gnupg lsb-release
   ```
3. Add Docker’s official GPG key:
   ```bash
   sudo mkdir -p /etc/apt/keyrings
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
   ```
4. Set up the Docker repository:
   ```bash
   echo \
     "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
     $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   ```
5. Install Docker Engine:
   ```bash
   sudo apt update
   sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   ```
6. Verify Docker:
   ```bash
   sudo docker run hello-world
   ```

## Install Docker Compose

Docker Compose comes with the `docker compose` plugin installed above. Verify it with:

```bash
docker compose version
```

## Clone Repository

```bash
git clone <repository-url>
cd client-hunting-platform
```

## Configure backend/.env

Create or update `backend/.env` with the required settings for the backend. Example:

```env
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/client_hunting
```

## Run

```bash
docker compose up -d
```

## Verify

```bash
curl http://SERVER_IP:8000/health
```

## Useful commands

```bash
docker compose logs -f

docker compose restart

docker compose down
```
