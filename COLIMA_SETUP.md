# Colima Setup Guide

This project uses **Colima** instead of Docker Desktop for local development. Colima is a lightweight, CLI-based Docker runtime that provides full Docker compatibility without the overhead of Docker Desktop.

## Why Colima?

- ✅ **Lighter weight** - No GUI application, lower resource usage
- ✅ **Faster startup** - Starts in seconds vs minutes
- ✅ **CLI-only** - Better for automation and CI/CD
- ✅ **Full compatibility** - Works with all Docker commands and docker-compose
- ✅ **Free and open source**

## Installation

### macOS

1. **Install Homebrew** (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Colima and Docker CLI**:
   ```bash
   brew install colima docker docker-compose
   ```

3. **Start Colima**:
   ```bash
   colima start
   ```

4. **Verify installation**:
   ```bash
   colima status
   docker --version
   docker info
   ```

### Linux

```bash
# Install via Homebrew on Linux
brew install colima docker docker-compose

# Or use your distribution's package manager
# (Colima installation may vary by distribution)
```

## Basic Usage

```bash
# Start Colima
colima start

# Stop Colima
colima stop

# Restart Colima
colima restart

# Check status
colima status

# View logs
colima logs

# Delete Colima VM (removes all containers and data)
colima delete
```

## Configuration

### Custom Resource Allocation

By default, Colima allocates:
- 2 CPU cores
- 2GB RAM
- 60GB disk space

To customize these values:

```bash
# Stop Colima first
colima stop

# Start with custom resources
colima start --cpu 4 --memory 8

# Or specify disk space
colima start --cpu 4 --memory 8 --disk 100
```

### Using Different Runtime

Colima supports both Docker and containerd runtimes:

```bash
# Start with Docker runtime (default)
colima start --runtime docker

# Start with containerd runtime
colima start --runtime containerd
```

## Docker Context

Colima automatically creates a Docker context. To manage contexts:

```bash
# List all Docker contexts
docker context ls

# Use Colima context
docker context use colima

# Check current context
docker context show
```

If you have Docker Desktop installed, you may need to switch contexts:

```bash
# Switch to Colima
docker context use colima

# Switch back to Docker Desktop (if needed)
docker context use desktop-linux
```

## Troubleshooting

### Docker commands not working

If `docker` commands fail after installing Colima:

```bash
# Check Colima status
colima status

# Restart Colima
colima restart

# Verify Docker context
docker context show

# Switch to Colima context if needed
docker context use colima
```

### Port conflicts

If you get port conflicts, check what's using the ports:

```bash
# Check for port conflicts
lsof -i :8002
lsof -i :3002
lsof -i :5433

# Stop conflicting services or change ports in docker-compose.yml
```

### Colima won't start

If Colima fails to start:

```bash
# Check logs
colima logs

# Try deleting and recreating
colima delete
colima start

# Check system resources (Colima needs available CPU/RAM)
```

### Performance issues

If containers are slow, try allocating more resources:

```bash
colima stop
colima start --cpu 4 --memory 8
```

## Migration from Docker Desktop

If you're currently using Docker Desktop:

1. **Stop Docker Desktop**:
   - Quit Docker Desktop application
   - Or: `osascript -e 'quit app "Docker"'`

2. **Install Colima** (see Installation section)

3. **Switch Docker context**:
   ```bash
   docker context use colima
   ```

4. **Start Colima**:
   ```bash
   colima start
   ```

5. **Verify**:
   ```bash
   docker info
   docker ps
   ```

Your existing Docker images and containers from Docker Desktop won't be available in Colima (they're separate). You can:
- Pull images again as needed
- Export/import if you have important data

## Integration with This Project

The setup script (`setup-local-railway.sh`) automatically:
1. Checks for Colima installation
2. Installs Colima if needed
3. Starts Colima
4. Configures Docker context
5. Verifies Docker is working

Just run:
```bash
./setup-local-railway.sh
```

## Additional Resources

- [Colima GitHub](https://github.com/abiosoft/colima)
- [Colima Documentation](https://github.com/abiosoft/colima/blob/main/docs/README.md)
- [Docker Documentation](https://docs.docker.com/)

