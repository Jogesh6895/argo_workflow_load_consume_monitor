# Agent Guidelines for Argo Workflows Load-Consume-Monitor

## Build Commands

This project uses Docker for containerization and Argo Workflows for orchestration.

```bash
# Build Docker image
docker build -t argo-workflow-monitor .

# Run a specific workflow script locally (for testing)
python workflows/redis_job_loader_workflow/redis_job_loader.py
python workflows/redis_job_consumer_workflow/redis_job_consumer.py
python workflows/overall_monitoring_workflow/overall_monitoring.py -p "ARGO_STATUS:JOB_LOADER:" -c "current"

# Deploy to Kubernetes
kubectl apply -f redis-service.yaml
kubectl apply -f workflows/*/scheduled_*.yaml
```

**Note:** This project does not have automated testing or linting configured. Before running scripts manually, ensure Redis is accessible.

## Security Guidelines

### Environment Variables
Always use environment variables for sensitive data (passwords, API keys, tokens):
- Never hardcode credentials in source code
- Use `os.getenv()` with default values for optional configuration
- Validate required environment variables before execution

```python
import os

REDIS_CONNECTION_DICT = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", 6379)),
    "username": os.getenv("REDIS_USERNAME", ""),
    "password": os.getenv("REDIS_PASSWORD"),  # Required, no default
    "db": int(os.getenv("REDIS_DB", 0)),
}

if __name__ == "__main__":
    if not REDIS_CONNECTION_DICT["password"]:
        raise ValueError("REDIS_PASSWORD environment variable is required")
```

### .env Files
- Use `.env` files for local development (add to `.gitignore`)
- Create `.env.example` as a template with placeholder values
- Commit `.env.example` but never commit `.env`

### Code Review
Before committing code, search for sensitive patterns:
```bash
# Check for passwords
git grep -i "password\|secret\|api_key\|token"

# Check for IP addresses
git grep -E "\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
```

### Git History
- For public repositories, fix security issues **before** initializing git
- If credentials are already committed, use `git filter-repo` to rewrite history
- Never commit secrets to public repositories, even if later deleted

## Code Style Guidelines

### Import Organization
Group imports in this order:
1. Standard library imports (sys, time, datetime, etc.)
2. Third-party imports (redis, etc.)
3. Local imports (if any)

```python
import sys
import time
import datetime
import redis
from optparse import OptionParser
```

### Naming Conventions
- **Global Constants**: ALL_CAPS with underscores
  ```python
  REDIS_CONNECTION_DICT = {}
  STATUS_KEY_TTL = 14400
  REDIS_JOB_QUEUE_KEY = "queue:argo_job_queue"
  CURRENT_YEARWEEK = "%04d%02d" % (NOW_TIME_OBJ.year, NOW_TIME_OBJ.isocalendar()[1])
  ```
- **Functions**: snake_case
  ```python
  def load_jobs():
  def consume_jobs():
  def monitor(pattern, check_option):
  ```
- **Variables**: snake_case
  ```python
  redis_connection = redis.Redis(**REDIS_CONNECTION_DICT)
  job_val = "job_" + str(i)
  time_taken = end_time - start_time
  ```

### Module-Level Constants
Define all configuration constants at module level before functions:
- Connection parameters (host, port, password, db)
- Time-related constants (TTL, sleep intervals)
- Redis key patterns (queue names, status key prefixes)
- Computed time values (CURRENT_YEARWEEK, PREVIOUS_YEARWEEK)

### Error Handling
Wrap Redis operations in try-except blocks:
```python
try:
    redis_connection = redis.Redis(**REDIS_CONNECTION_DICT)
    # Redis operations here
except Exception as e:
    print("Exception Occured: %s" % (e))
```

**Important:** The current pattern only prints errors and continues. Consider:
- Logging errors instead of print statements
- Retrying transient Redis failures
- Exiting with non-zero status for critical failures

### Redis Connection Pattern
Create new Redis connection for each function call:
```python
redis_connection = redis.Redis(**REDIS_CONNECTION_DICT)
# Use connection
redis_connection.lpush(key, value)
redis_connection.rpop(key)
redis_connection.setex(key, ttl, value)
redis_connection.get(key)
```

### Main Entry Point
Always guard main execution:
```python
if __name__ == "__main__":
    start_time = time.time()
    # Main logic here
    end_time = time.time()
    time_taken = end_time - start_time
    print("Total Time Taken: ", time_taken, "seconds")
```

### Time Tracking
Measure execution time for all workflow scripts:
- Capture `start_time` before main logic
- Capture `end_time` after main logic
- Print total time taken

### CLI Arguments (for monitoring workflow)
Use `optparse` for command-line arguments:
```python
parser = OptionParser()
parser.add_option('-p', '--pattern', dest='pattern', action='store', help='base pattern to check')
parser.add_option('-c', '--check', dest='check', action='store', help='[current/previous] week')
(options, args) = parser.parse_args()
```

## Project Structure

```
.
├── Dockerfile                              # Container image definition
├── redis-service.yaml                      # Kubernetes service for Redis
├── requirements.txt                        # Python dependencies
└── workflows/
    ├── redis_job_loader_workflow/
    │   ├── redis_job_loader.py            # Job producer script
    │   ├── redis_job_loader_workflow.yaml # Manual workflow template
    │   └── scheduled_redis_job_loader_workflow.yaml  # Cron workflow (every 3 min)
    ├── redis_job_consumer_workflow/
    │   ├── redis_job_consumer.py          # Job consumer script
    │   ├── redis_job_consumer_workflow.yaml
    │   └── scheduled_redis_job_consumer_workflow.yaml # Cron workflow (every 1 min)
    └── overall_monitoring_workflow/
        ├── overall_monitoring.py           # Health check script
        ├── overall_monitoring_workflow.yaml
        └── scheduled_overall_monitoring_workflow.yaml # Cron workflow (every 5 min)
```

## Known Issues to Address

1. **Job imbalance**: Loader pushes 10 jobs, consumer only pops 5. Queue will grow indefinitely.
2. **No retry logic**: Redis failures are not retried; operations silently fail.
3. **Error handling**: Only prints errors; no proper logging or status codes.
4. **Old CLI library**: Consider migrating from `optparse` to `argparse`.

## Workflow Patterns

When adding new workflows:
1. Create directory under `workflows/`
2. Write Python script following naming: `<workflow_name>.py`
3. Create manual workflow template: `<workflow_name>_workflow.yaml`
4. Create scheduled workflow template: `scheduled_<workflow_name>_workflow.yaml`
5. Follow existing Cron schedule patterns (every 1 min, 3 min, 5 min)

## Redis Key Naming

- Job queue: `queue:argo_job_queue`
- Status keys: `ARGO_STATUS:<WORKFLOW_NAME>:<YEARWEEK>`
- TTL: 14400 seconds (4 hours)
- YEARWEEK format: `YYYYWW` (ISO week number)
