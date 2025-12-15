# Docker Deployment

Docker container for MaSIF-neosurf development and testing.

## Files

- `Dockerfile` - Docker image definition

## Building

```bash
docker build -t masif-neosurf:latest .
```

## Usage

### Interactive Shell

```bash
docker run -it masif-neosurf:latest /bin/bash
```

### Run Preprocessing

```bash
docker run -v $PWD:/data masif-neosurf:latest masif-preprocess /data/input.pdb CHAIN_ID
```

### With Volume Mounts

```bash
docker run \
  -v /path/to/input:/input \
  -v /path/to/output:/output \
  masif-neosurf:latest \
  masif-preprocess /input/file.pdb CHAIN_ID -o /output
```

## Development

### Build with Custom Tag

```bash
docker build -t masif-neosurf:dev .
```

### Run with Code Mount (for development)

```bash
docker run -it \
  -v $PWD:/workspace \
  masif-neosurf:dev \
  /bin/bash
```

## Publishing

### To Docker Hub

```bash
docker tag masif-neosurf:latest your-username/masif-neosurf:latest
docker push your-username/masif-neosurf:latest
```

### To Private Registry

```bash
docker tag masif-neosurf:latest registry.example.com/masif-neosurf:latest
docker push registry.example.com/masif-neosurf:latest
```

## Notes

⚠️ **Docker is typically not available on HPC clusters.** Use Singularity instead for HPC environments.

Docker is best suited for:
- Local development
- Testing
- CI/CD pipelines
- Cloud deployments
