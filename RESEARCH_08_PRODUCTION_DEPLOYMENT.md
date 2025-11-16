# Betfair MCP Server - Production Deployment

**Document:** RESEARCH_08_PRODUCTION_DEPLOYMENT.md
**Part of:** Betfair MCP Server Research Series
**Status:** ✅ Complete
**Last Updated:** 2025-11-16

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Deployment Architectures](#deployment-architectures)
3. [Docker Containerization](#docker-containerization)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [CI/CD Pipeline](#cicd-pipeline)
6. [Monitoring & Observability](#monitoring--observability)
7. [Logging](#logging)
8. [Security Hardening](#security-hardening)
9. [Secrets Management](#secrets-management)
10. [Health Checks & Reliability](#health-checks--reliability)
11. [Scaling Strategies](#scaling-strategies)
12. [References](#references)

---

## Executive Summary

**Production deployment of MCP servers requires enterprise-grade infrastructure.**

**Deployment Options:**
1. **Local (stdio)** - Development & personal use (MVP)
2. **Docker** - Consistent deployment across environments
3. **Kubernetes** - Production-grade scalability & reliability
4. **Cloud Platforms** - AWS ECS, Google Cloud Run, Azure Container Instances

**Key Infrastructure:**
- ✅ **Containerization** - Docker for consistency
- ✅ **Orchestration** - Kubernetes for multi-user deployment
- ✅ **CI/CD** - GitHub Actions for automated testing & deployment
- ✅ **Monitoring** - Prometheus + Grafana
- ✅ **Logging** - ELK Stack (Elasticsearch, Logstash, Kibana)
- ✅ **Secrets** - HashiCorp Vault or cloud-native solutions
- ✅ **Security** - HTTPS, RBAC, network policies

**Critical Findings:**
- StatefulSets recommended for MCP servers (maintain session state)
- Health checks essential (startup, liveness, readiness probes)
- Distributed tracing helps debug multi-server deployments
- Rate limiting at infrastructure level prevents abuse

---

## Deployment Architectures

### Architecture 1: Local Development (stdio)

```
┌──────────────────┐
│  Claude Desktop  │
│    (MCP Client)  │
└────────┬─────────┘
         │ stdio
         ▼
┌──────────────────┐
│  betfair-mcp     │
│  (Local Process) │
└────────┬─────────┘
         │ HTTPS
         ▼
┌──────────────────┐
│  Betfair API     │
└──────────────────┘
```

**Use Case:** Personal use, development, testing
**Pros:** Simple, low latency, no network overhead
**Cons:** Single user, no remote access

---

### Architecture 2: Single Docker Container

```
┌──────────────────┐
│   AI Client      │
│  (HTTP/SSE)      │
└────────┬─────────┘
         │ HTTPS
         ▼
┌──────────────────┐
│  Docker Host     │
│  ┌────────────┐  │
│  │ betfair-mcp│  │
│  │ Container  │  │
│  └────────────┘  │
└────────┬─────────┘
         │ HTTPS
         ▼
┌──────────────────┐
│  Betfair API     │
└──────────────────┘
```

**Use Case:** Small team, single server deployment
**Pros:** Portable, consistent environment
**Cons:** Single point of failure, limited scaling

---

### Architecture 3: Kubernetes Cluster (Production)

```
┌───────────────────────────────────────────────┐
│          Kubernetes Cluster                   │
│                                               │
│  ┌─────────────────────────────────────────┐ │
│  │          Ingress Controller             │ │
│  │         (HTTPS, Load Balancer)          │ │
│  └──────────────┬──────────────────────────┘ │
│                 │                             │
│  ┌──────────────▼──────────────┐             │
│  │    Service (betfair-mcp)    │             │
│  └──────────────┬──────────────┘             │
│                 │                             │
│  ┌──────────────▼──────────────┐             │
│  │     StatefulSet (3 pods)    │             │
│  │  ┌─────────┐ ┌─────────┐   │             │
│  │  │  Pod 1  │ │  Pod 2  │   │             │
│  │  │betfair- │ │betfair- │   │             │
│  │  │  mcp    │ │  mcp    │   │             │
│  │  └─────────┘ └─────────┘   │             │
│  └─────────────────────────────┘             │
│                                               │
│  ┌─────────────────────────────────────────┐ │
│  │      Persistent Volumes                 │ │
│  │  (Session state, cache, logs)           │ │
│  └─────────────────────────────────────────┘ │
│                                               │
│  ┌─────────────────────────────────────────┐ │
│  │     Monitoring & Logging                │ │
│  │  (Prometheus, Grafana, ELK)             │ │
│  └─────────────────────────────────────────┘ │
└───────────────────────────────────────────────┘
```

**Use Case:** Multi-user, high availability, production
**Pros:** Scalable, resilient, enterprise-grade
**Cons:** Complex setup, higher cost

---

## Docker Containerization

### Dockerfile

```dockerfile
# Multi-stage build for smaller image
FROM python:3.11-slim as builder

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY src/ ./src/
COPY README.md CLAUDE.md ./

# Create non-root user
RUN useradd -m -u 1000 betfair && \
    chown -R betfair:betfair /app

USER betfair

# Set environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Expose port (if using HTTP transport)
EXPOSE 8000

# Run server
CMD ["python", "-m", "betfair_mcp.server"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  betfair-mcp:
    build:
      context: .
      dockerfile: Dockerfile
    image: betfair-mcp:latest
    container_name: betfair-mcp-server
    restart: unless-stopped

    # Environment variables
    environment:
      - BETFAIR_USERNAME=${BETFAIR_USERNAME}
      - BETFAIR_PASSWORD=${BETFAIR_PASSWORD}
      - BETFAIR_APP_KEY=${BETFAIR_APP_KEY}
      - BETFAIR_CERTS_PATH=/certs
      - LOG_LEVEL=INFO
      - TRANSPORT=http
      - PORT=8000

    # Mount secrets (read-only)
    volumes:
      - ./certs:/certs:ro
      - ./logs:/app/logs
      - cache-volume:/app/cache

    # Network
    ports:
      - "8000:8000"
    networks:
      - betfair-network

    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

    # Health check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Prometheus for monitoring
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - betfair-network

  # Grafana for visualization
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/dashboards:/etc/grafana/provisioning/dashboards:ro
    ports:
      - "3000:3000"
    networks:
      - betfair-network
    depends_on:
      - prometheus

volumes:
  cache-volume:
  prometheus-data:
  grafana-data:

networks:
  betfair-network:
    driver: bridge
```

### Build & Run

```bash
# Build image
docker build -t betfair-mcp:latest .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f betfair-mcp

# Stop
docker-compose down
```

---

## Kubernetes Deployment

### Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: betfair-mcp
  labels:
    name: betfair-mcp
```

### Secret Management

```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: betfair-credentials
  namespace: betfair-mcp
type: Opaque
stringData:
  username: "your_username"
  password: "your_password"
  app_key: "your_app_key"
```

**Better: Use External Secrets Operator**
```yaml
# external-secret.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: betfair-credentials
  namespace: betfair-mcp
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: betfair-credentials
  data:
    - secretKey: username
      remoteRef:
        key: betfair/credentials
        property: username
    - secretKey: password
      remoteRef:
        key: betfair/credentials
        property: password
    - secretKey: app_key
      remoteRef:
        key: betfair/credentials
        property: app_key
```

### ConfigMap

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: betfair-mcp-config
  namespace: betfair-mcp
data:
  LOG_LEVEL: "INFO"
  TRANSPORT: "http"
  PORT: "8000"
  BETFAIR_ENV: "production"
```

### StatefulSet

```yaml
# statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: betfair-mcp
  namespace: betfair-mcp
spec:
  serviceName: betfair-mcp
  replicas: 3
  selector:
    matchLabels:
      app: betfair-mcp
  template:
    metadata:
      labels:
        app: betfair-mcp
    spec:
      serviceAccountName: betfair-mcp

      # Security context
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000

      containers:
      - name: betfair-mcp
        image: betfair-mcp:1.0.0
        imagePullPolicy: IfNotPresent

        ports:
        - containerPort: 8000
          name: http

        # Environment from ConfigMap
        envFrom:
        - configMapRef:
            name: betfair-mcp-config

        # Environment from Secret
        env:
        - name: BETFAIR_USERNAME
          valueFrom:
            secretKeyRef:
              name: betfair-credentials
              key: username
        - name: BETFAIR_PASSWORD
          valueFrom:
            secretKeyRef:
              name: betfair-credentials
              key: password
        - name: BETFAIR_APP_KEY
          valueFrom:
            secretKeyRef:
              name: betfair-credentials
              key: app_key

        # Resource limits
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "2000m"

        # Health checks
        startupProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          failureThreshold: 30

        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
          timeoutSeconds: 5
          failureThreshold: 3

        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 5

        # Volume mounts
        volumeMounts:
        - name: cache
          mountPath: /app/cache
        - name: logs
          mountPath: /app/logs
        - name: certs
          mountPath: /certs
          readOnly: true

      # Volumes
      volumes:
      - name: certs
        secret:
          secretName: betfair-ssl-certs

  # Persistent volume claims
  volumeClaimTemplates:
  - metadata:
      name: cache
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 1Gi
  - metadata:
      name: logs
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 5Gi
```

### Service

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: betfair-mcp
  namespace: betfair-mcp
spec:
  selector:
    app: betfair-mcp
  ports:
  - name: http
    port: 80
    targetPort: 8000
  type: ClusterIP
```

### Ingress

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: betfair-mcp
  namespace: betfair-mcp
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - betfair-mcp.example.com
    secretName: betfair-mcp-tls
  rules:
  - host: betfair-mcp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: betfair-mcp
            port:
              number: 80
```

### Deploy to Kubernetes

```bash
# Apply namespace
kubectl apply -f namespace.yaml

# Apply secrets (use sealed-secrets or external-secrets in production)
kubectl apply -f secret.yaml

# Apply config
kubectl apply -f configmap.yaml

# Deploy StatefulSet
kubectl apply -f statefulset.yaml

# Create service
kubectl apply -f service.yaml

# Create ingress
kubectl apply -f ingress.yaml

# Check status
kubectl get pods -n betfair-mcp
kubectl logs -f -n betfair-mcp betfair-mcp-0

# Scale
kubectl scale statefulset betfair-mcp --replicas=5 -n betfair-mcp
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Build and Deploy

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install uv
          uv sync

      - name: Run tests
        run: |
          uv run pytest tests/ --cov=betfair_mcp

      - name: Lint
        run: |
          uv run ruff check .
          uv run black --check .

      - name: Type check
        run: |
          uv run mypy src/

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=sha

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Set up kubectl
        uses: azure/setup-kubectl@v3

      - name: Configure kubectl
        run: |
          echo "${{ secrets.KUBECONFIG }}" > kubeconfig.yaml
          export KUBECONFIG=kubeconfig.yaml

      - name: Update deployment
        run: |
          kubectl set image statefulset/betfair-mcp \
            betfair-mcp=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:sha-${{ github.sha }} \
            -n betfair-mcp

      - name: Wait for rollout
        run: |
          kubectl rollout status statefulset/betfair-mcp -n betfair-mcp --timeout=5m
```

---

## Monitoring & Observability

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'betfair-mcp'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - betfair-mcp
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: betfair-mcp
      - source_labels: [__meta_kubernetes_pod_ip]
        action: replace
        target_label: __address__
        replacement: $1:8000
```

### Application Metrics

```python
# src/betfair_mcp/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Define metrics
tool_calls_total = Counter(
    'mcp_tool_calls_total',
    'Total tool calls',
    ['tool_name', 'status']
)

tool_duration_seconds = Histogram(
    'mcp_tool_duration_seconds',
    'Tool execution duration',
    ['tool_name']
)

active_sessions = Gauge(
    'mcp_active_sessions',
    'Number of active MCP sessions'
)

betfair_api_calls = Counter(
    'betfair_api_calls_total',
    'Total Betfair API calls',
    ['endpoint', 'status']
)

cache_hits = Counter(
    'mcp_cache_hits_total',
    'Cache hits',
    ['cache_type']
)

# Instrument tools
@mcp.tool()
@tool_duration_seconds.labels(tool_name='get_markets').time()
async def get_markets():
    """Get markets with metrics"""
    try:
        result = await asyncio.to_thread(betfair_client.betting.list_markets)
        tool_calls_total.labels(tool_name='get_markets', status='success').inc()
        return result
    except Exception as e:
        tool_calls_total.labels(tool_name='get_markets', status='error').inc()
        raise

# Expose metrics endpoint
from fastapi import FastAPI
app = FastAPI()

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Betfair MCP Server",
    "panels": [
      {
        "title": "Tool Calls per Minute",
        "targets": [{
          "expr": "rate(mcp_tool_calls_total[1m])"
        }]
      },
      {
        "title": "Tool Success Rate",
        "targets": [{
          "expr": "sum(rate(mcp_tool_calls_total{status='success'}[5m])) / sum(rate(mcp_tool_calls_total[5m])) * 100"
        }]
      },
      {
        "title": "Betfair API Latency",
        "targets": [{
          "expr": "histogram_quantile(0.95, rate(mcp_tool_duration_seconds_bucket[5m]))"
        }]
      },
      {
        "title": "Active Sessions",
        "targets": [{
          "expr": "mcp_active_sessions"
        }]
      }
    ]
  }
}
```

---

## Logging

### Structured Logging

```python
# src/betfair_mcp/logging_config.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """JSON log formatter"""

    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception info
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'user_id'):
            log_obj['user_id'] = record.user_id
        if hasattr(record, 'tool_name'):
            log_obj['tool_name'] = record.tool_name

        return json.dumps(log_obj)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/betfair-mcp.log')
    ]
)

# Set JSON formatter
for handler in logging.root.handlers:
    handler.setFormatter(JSONFormatter())

logger = logging.getLogger(__name__)
```

### ELK Stack Integration

```yaml
# filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /app/logs/*.log
    json.keys_under_root: true
    json.add_error_key: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "betfair-mcp-%{+yyyy.MM.dd}"

setup.kibana:
  host: "kibana:5601"
```

---

## Security Hardening

### Network Policies

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: betfair-mcp-policy
  namespace: betfair-mcp
spec:
  podSelector:
    matchLabels:
      app: betfair-mcp
  policyTypes:
  - Ingress
  - Egress

  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: nginx-ingress
    ports:
    - protocol: TCP
      port: 8000

  egress:
  - to:
    - podSelector:
        matchLabels:
          app: prometheus
    ports:
    - protocol: TCP
      port: 9090
  - to:  # Allow Betfair API
    ports:
    - protocol: TCP
      port: 443
  - to:  # Allow DNS
    - namespaceSelector: {}
    ports:
    - protocol: UDP
      port: 53
```

### Pod Security Policy

```yaml
# pod-security-policy.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: betfair-mcp-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'persistentVolumeClaim'
  hostNetwork: false
  hostIPC: false
  hostPID: false
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
  readOnlyRootFilesystem: false
```

---

## Secrets Management

### HashiCorp Vault

```python
# src/betfair_mcp/secrets.py
import hvac
import os

class VaultSecrets:
    """Retrieve secrets from Vault"""

    def __init__(self):
        self.client = hvac.Client(
            url=os.getenv('VAULT_ADDR'),
            token=os.getenv('VAULT_TOKEN')
        )

    def get_betfair_credentials(self):
        """Get Betfair credentials from Vault"""
        secret = self.client.secrets.kv.v2.read_secret(
            path='betfair/credentials',
            mount_point='secret'
        )

        return {
            'username': secret['data']['data']['username'],
            'password': secret['data']['data']['password'],
            'app_key': secret['data']['data']['app_key']
        }
```

---

## Health Checks & Reliability

### Health Check Endpoints

```python
# src/betfair_mcp/health.py
from fastapi import FastAPI, Response
import asyncio

app = FastAPI()

@app.get("/health")
async def health():
    """Liveness probe - is the server running?"""
    return {"status": "healthy"}

@app.get("/ready")
async def ready():
    """Readiness probe - is the server ready to serve requests?"""
    try:
        # Check Betfair connection
        await asyncio.to_thread(betfair_client.account.get_account_funds)
        return {"status": "ready"}
    except Exception as e:
        return Response(
            content=f"Not ready: {str(e)}",
            status_code=503
        )

@app.get("/startup")
async def startup():
    """Startup probe - has initialization completed?"""
    if betfair_client.session_token:
        return {"status": "started"}
    else:
        return Response(
            content="Still initializing",
            status_code=503
        )
```

---

## Scaling Strategies

### Horizontal Pod Autoscaler

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: betfair-mcp-hpa
  namespace: betfair-mcp
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: StatefulSet
    name: betfair-mcp
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: mcp_tool_calls_per_second
      target:
        type: AverageValue
        averageValue: "100"
```

---

## References

### Infrastructure Tools
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Prometheus](https://prometheus.io/docs/)
- [Grafana](https://grafana.com/docs/)

### Related Research Documents
- [RESEARCH_05_FASTMCP_INTEGRATION.md](./RESEARCH_05_FASTMCP_INTEGRATION.md) - Server implementation
- [RESEARCH_07_COMPLIANCE.md](./RESEARCH_07_COMPLIANCE.md) - Security requirements
- [RESEARCH_02_RATE_LIMITS.md](./RESEARCH_02_RATE_LIMITS.md) - Infrastructure-level rate limiting

---

**Previous Document:** [RESEARCH_07_COMPLIANCE.md](./RESEARCH_07_COMPLIANCE.md)
**Back to:** [RESEARCH_INDEX.md](./RESEARCH_INDEX.md)
