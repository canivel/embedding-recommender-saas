# Team Epsilon: Control Plane

## Mission
Build the orchestration layer that manages training pipelines, deployment automation, resource scaling, and infrastructure as code.

## Technology Stack
- **Container Orchestration**: Kubernetes (EKS/GKE)
- **Workflow Orchestration**: Apache Airflow 2.7+
- **Infrastructure as Code**: Terraform or Pulumi
- **CI/CD**: GitHub Actions + ArgoCD
- **Container Registry**: ECR or GCR
- **Secrets Management**: AWS Secrets Manager or Vault

## Core Components

### 1. Training Orchestration (Airflow)

**DAGs:**

#### `tenant_model_training.py`
```python
from airflow import DAG
from airflow.providers.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'ml-team',
    'depends_on_past': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'tenant_model_training',
    default_args=default_args,
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    catchup=False,
) as dag:

    # Task 1: Prepare training data
    prepare_data = KubernetesPodOperator(
        task_id='prepare_training_data',
        name='prepare-data',
        namespace='ml-jobs',
        image='data-pipeline:latest',
        arguments=[
            '--tenant-id', '{{ params.tenant_id }}',
            '--output', 's3://bucket/{{ params.tenant_id }}/training_data/'
        ],
        resources={'request_memory': '2Gi', 'request_cpu': '1'},
    )

    # Task 2: Train model
    train_model = KubernetesPodOperator(
        task_id='train_model',
        name='train-model',
        namespace='ml-jobs',
        image='ml-engine:latest',
        arguments=[
            '--tenant-id', '{{ params.tenant_id }}',
            '--model-type', '{{ params.model_type }}',
            '--epochs', '10'
        ],
        resources={'request_memory': '8Gi', 'request_cpu': '4'},
    )

    # Task 3: Build FAISS index
    build_index = KubernetesPodOperator(
        task_id='build_faiss_index',
        name='build-index',
        namespace='ml-jobs',
        image='ml-engine:latest',
        arguments=['--tenant-id', '{{ params.tenant_id }}', '--build-index'],
        resources={'request_memory': '4Gi', 'request_cpu': '2'},
    )

    # Task 4: Deploy to production
    deploy_model = KubernetesPodOperator(
        task_id='deploy_model',
        name='deploy-model',
        namespace='ml-jobs',
        image='deployer:latest',
        arguments=[
            '--tenant-id', '{{ params.tenant_id }}',
            '--model-path', 's3://bucket/{{ params.tenant_id }}/model.pth'
        ],
    )

    # Task 5: Update embeddings in Redis
    update_cache = KubernetesPodOperator(
        task_id='update_redis_cache',
        name='update-cache',
        namespace='ml-jobs',
        image='ml-engine:latest',
        arguments=['--tenant-id', '{{ params.tenant_id }}', '--refresh-cache'],
    )

    prepare_data >> train_model >> build_index >> [deploy_model, update_cache]
```

#### `data_quality_check.py`
```python
with DAG(
    'data_quality_check',
    schedule_interval='0 * * * *',  # Hourly
    catchup=False,
) as dag:

    check_completeness = PythonOperator(
        task_id='check_data_completeness',
        python_callable=check_missing_data,
    )

    check_freshness = PythonOperator(
        task_id='check_data_freshness',
        python_callable=check_stale_data,
    )

    check_anomalies = PythonOperator(
        task_id='check_anomalies',
        python_callable=detect_anomalies,
    )

    [check_completeness, check_freshness, check_anomalies]
```

### 2. Kubernetes Configuration

#### Namespace Structure
```yaml
# namespaces.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
---
apiVersion: v1
kind: Namespace
metadata:
  name: staging
---
apiVersion: v1
kind: Namespace
metadata:
  name: ml-jobs
```

#### Auto-Scaling
```yaml
# backend-api-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-api-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend-api
  minReplicas: 3
  maxReplicas: 20
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
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # 5 min cooldown
    scaleUp:
      stabilizationWindowSeconds: 60
```

### 3. Infrastructure as Code (Terraform)

```hcl
# main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# EKS Cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "embeddings-saas-cluster"
  cluster_version = "1.28"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    general = {
      desired_size = 3
      min_size     = 2
      max_size     = 10
      instance_types = ["t3.large"]
      capacity_type  = "SPOT"  # Cost savings
    }
    ml_workloads = {
      desired_size = 1
      min_size     = 1
      max_size     = 5
      instance_types = ["c5.2xlarge"]
      capacity_type  = "ON_DEMAND"
    }
  }
}

# RDS PostgreSQL
resource "aws_db_instance" "postgres" {
  identifier           = "embeddings-saas-db"
  engine               = "postgres"
  engine_version       = "15.4"
  instance_class       = "db.t3.medium"
  allocated_storage    = 100
  storage_encrypted    = true
  multi_az             = true
  db_name              = "embeddings_saas"
  username             = var.db_username
  password             = var.db_password
  skip_final_snapshot  = false
  backup_retention_period = 7
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "embeddings-cache"
  engine               = "redis"
  node_type            = "cache.t3.medium"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
}

# S3 Buckets
resource "aws_s3_bucket" "data_lake" {
  bucket = "embeddings-saas-data"
  versioning {
    enabled = true
  }
  lifecycle_rule {
    enabled = true
    transition {
      days          = 30
      storage_class = "INTELLIGENT_TIERING"
    }
  }
}
```

### 4. CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/deploy.yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2

      - name: Login to ECR
        run: |
          aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin ${{ secrets.ECR_REGISTRY }}

      - name: Build and push backend-api
        run: |
          docker build -t backend-api:${{ github.sha }} ./backend-api
          docker tag backend-api:${{ github.sha }} ${{ secrets.ECR_REGISTRY }}/backend-api:latest
          docker push ${{ secrets.ECR_REGISTRY }}/backend-api:latest

      - name: Build and push ml-engine
        run: |
          docker build -t ml-engine:${{ github.sha }} ./ml-engine
          docker push ${{ secrets.ECR_REGISTRY }}/ml-engine:latest

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - name: Deploy via ArgoCD
        run: |
          argocd app sync embeddings-saas-production --server ${{ secrets.ARGOCD_SERVER }} --auth-token ${{ secrets.ARGOCD_TOKEN }}

      - name: Wait for rollout
        run: |
          kubectl rollout status deployment/backend-api -n production --timeout=5m
          kubectl rollout status deployment/ml-engine -n production --timeout=5m

  smoke-tests:
    needs: deploy
    runs-on: ubuntu-latest
    steps:
      - name: Run smoke tests
        run: |
          curl -f https://api.example.com/health || exit 1
          curl -f https://api.example.com/ready || exit 1
```

### 5. GitOps (ArgoCD)

```yaml
# argocd/production-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: embeddings-saas-production
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/yourorg/embeddings-saas
    targetRevision: main
    path: k8s/production
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

### 6. Monitoring & Alerting Setup

```yaml
# prometheus/prometheus-config.yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true

  - job_name: 'backend-api'
    static_configs:
      - targets: ['backend-api.production.svc.cluster.local:9090']

  - job_name: 'ml-engine'
    static_configs:
      - targets: ['ml-engine.production.svc.cluster.local:9090']
```

### 7. Disaster Recovery

**Backup Strategy:**
- Database: Automated daily snapshots (7 day retention)
- S3: Versioning enabled + cross-region replication
- Configuration: Git as source of truth

**Recovery Procedures:**
```bash
# Restore database from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier embeddings-saas-db-restored \
  --db-snapshot-identifier snapshot-2025-01-07

# Restore Kubernetes resources
kubectl apply -f k8s/production/

# Restore S3 data
aws s3 sync s3://backup-bucket/ s3://embeddings-saas-data/
```

## Cost Optimization

### 1. Spot Instances for Non-Critical Workloads
- Use Spot for training jobs (60-70% cost savings)
- Fallback to On-Demand if Spot unavailable

### 2. Auto-Scaling Policies
- Scale down during low-traffic hours
- Predictive scaling based on historical patterns

### 3. S3 Lifecycle Policies
- Move cold data to Glacier after 90 days
- Delete old logs after 1 year

### 4. Reserved Instances
- Purchase 1-year RIs for baseline capacity
- 30-40% savings on steady-state workloads

## Success Criteria
- Zero-downtime deployments (blue-green)
- Training pipeline success rate > 95%
- Infrastructure provisioning time < 30 min
- Disaster recovery RTO < 4 hours, RPO < 1 hour
- Cost per API call < $0.001

## Development Workflow

### Phase 1 (Weeks 1-2)
- [ ] Terraform infrastructure setup
- [ ] Kubernetes cluster provisioning
- [ ] Basic Airflow DAGs
- [ ] CI/CD pipeline

### Phase 2 (Weeks 3-4)
- [ ] Training orchestration
- [ ] Auto-scaling policies
- [ ] Monitoring setup
- [ ] ArgoCD GitOps

### Phase 3 (Weeks 5-6)
- [ ] Disaster recovery procedures
- [ ] Cost optimization
- [ ] Advanced observability
- [ ] Security hardening
