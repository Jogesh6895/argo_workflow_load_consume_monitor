# Argo Workflows Load-Consume-Monitor

A distributed job processing system using Argo Workflows for orchestration and Redis as message queue middleware.

## Overview

This project demonstrates a three-component system:
- **Job Loader** (producer): Pushes jobs to a Redis queue every 3 minutes
- **Job Consumer** (processor): Consumes jobs from the Redis queue every 1 minute
- **Monitoring**: Health checks workflow status via Redis keys every 5 minutes

## Prerequisites

- Docker
- Kubernetes cluster with Argo Workflows installed
- Redis instance (or deploy via provided service manifest)

## Quick Start

```bash
# Build Docker image
docker build -t argo-workflow-monitor .

# Deploy Redis service
kubectl apply -f redis-service.yaml

# Deploy all scheduled workflows
kubectl apply -f workflows/*/scheduled_*.yaml
```

## Project Structure

```
.
├── Dockerfile                              # Container image definition
├── redis-service.yaml                      # Kubernetes service for Redis
├── requirements.txt                        # Python dependencies
└── workflows/
    ├── redis_job_loader_workflow/
    │   ├── redis_job_loader.py            # Job producer (10 jobs per run)
    │   ├── redis_job_loader_workflow.yaml # Manual workflow template
    │   └── scheduled_redis_job_loader_workflow.yaml  # Cron: every 3 min
    ├── redis_job_consumer_workflow/
    │   ├── redis_job_consumer.py          # Job consumer (5 jobs per run)
    │   ├── redis_job_consumer_workflow.yaml
    │   └── scheduled_redis_job_consumer_workflow.yaml # Cron: every 1 min
    └── overall_monitoring_workflow/
        ├── overall_monitoring.py           # Health check script
        ├── overall_monitoring_workflow.yaml
        └── scheduled_overall_monitoring_workflow.yaml # Cron: every 5 min
```

## Local Testing

Run individual workflows manually (requires accessible Redis instance):

```bash
# Set environment variables (or use .env file)
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=<your_redis_password>

# Test job loader
python workflows/redis_job_loader_workflow/redis_job_loader.py

# Test job consumer
python workflows/redis_job_consumer_workflow/redis_job_consumer.py

# Test monitoring
python workflows/overall_monitoring_workflow/overall_monitoring.py -p "ARGO_STATUS:JOB_LOADER:" -c "current"
```

## Configuration

Redis connection is configured via environment variables:

```python
REDIS_CONNECTION_DICT = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", 6379)),
    "username": os.getenv("REDIS_USERNAME", ""),
    "password": os.getenv("REDIS_PASSWORD"),
    "db": int(os.getenv("REDIS_DB", 0)),
}
```

**Note:** Set environment variables before running workflows. Use `.env.example` as a template:

```bash
# Copy example to .env and fill in your values
cp .env.example .env

# Source the environment file
export $(cat .env | xargs)
```

## Security

**Important:** This project is designed to be safe for public repositories. No sensitive data is hardcoded in the code.

- All credentials are loaded from environment variables
- `.env` file is excluded from git (see `.gitignore:41-42`)
- Only `.env.example` template is committed with placeholder values
- Scripts validate that `REDIS_PASSWORD` is set before execution

When deploying:
- Use Kubernetes secrets or config maps for environment variables
- Never commit actual credentials to the repository
- Rotate Redis passwords regularly

## Redis Key Naming

- **Job queue**: `queue:argo_job_queue`
- **Status keys**: `ARGO_STATUS:<WORKFLOW_NAME>:<YEARWEEK>`
- **TTL**: 14400 seconds (4 hours)
- **YEARWEEK format**: `YYYYWW` (ISO week number)

## Workflow Schedules

| Workflow | Schedule | Action |
|----------|----------|--------|
| Job Loader | Every 3 minutes | Pushes 10 jobs to queue |
| Job Consumer | Every 1 minute | Pops 5 jobs from queue |
| Monitoring | Every 5 minutes | Checks workflow status keys |

## Known Issues

1. **Job imbalance**: Loader pushes 10 jobs, consumer only pops 5 (queue grows indefinitely)
2. **No retry logic**: Redis failures are not retried
3. **Error handling**: Only prints errors, no proper logging
4. **Old CLI library**: Uses `optparse` instead of `argparse`

## License

This project is a demonstration/prototype.
