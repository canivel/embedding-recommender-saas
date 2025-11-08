terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }

  # Backend configuration for state storage
  # Uncomment and configure for production use
  # backend "s3" {
  #   bucket = "embeddings-saas-terraform-state"
  #   key    = "production/terraform.tfstate"
  #   region = "us-west-2"
  #   encrypt = true
  #   dynamodb_table = "terraform-state-lock"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "embeddings-saas"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# VPC Module
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.project_name}-vpc"
  cidr = var.vpc_cidr

  azs             = var.availability_zones
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs

  enable_nat_gateway   = true
  single_nat_gateway   = var.environment == "dev" ? true : false
  enable_dns_hostnames = true
  enable_dns_support   = true

  # Enable VPC endpoints for AWS services (cost optimization)
  enable_s3_endpoint = true

  tags = {
    Name = "${var.project_name}-vpc"
  }

  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
  }
}

# EKS Cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "${var.project_name}-cluster"
  cluster_version = var.kubernetes_version

  vpc_id                   = module.vpc.vpc_id
  subnet_ids               = module.vpc.private_subnets
  control_plane_subnet_ids = module.vpc.private_subnets

  # Enable cluster addons
  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }

  # Cluster access
  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true

  # Node groups
  eks_managed_node_groups = {
    # General purpose node group
    general = {
      name           = "general-purpose"
      instance_types = var.general_node_instance_types

      min_size     = var.general_node_min_size
      max_size     = var.general_node_max_size
      desired_size = var.general_node_desired_size

      capacity_type = var.environment == "production" ? "ON_DEMAND" : "SPOT"

      labels = {
        workload = "general"
      }

      tags = {
        Name = "general-purpose-node"
      }
    }

    # ML workload node group
    ml_workloads = {
      name           = "ml-workloads"
      instance_types = var.ml_node_instance_types

      min_size     = var.ml_node_min_size
      max_size     = var.ml_node_max_size
      desired_size = var.ml_node_desired_size

      capacity_type = "ON_DEMAND"  # Always on-demand for ML workloads

      labels = {
        workload = "ml"
      }

      taints = [
        {
          key    = "workload"
          value  = "ml"
          effect = "NoSchedule"
        }
      ]

      tags = {
        Name = "ml-workload-node"
      }
    }
  }

  tags = {
    Name = "${var.project_name}-eks-cluster"
  }
}

# RDS PostgreSQL
resource "aws_db_subnet_group" "postgres" {
  name       = "${var.project_name}-postgres-subnet"
  subnet_ids = module.vpc.private_subnets

  tags = {
    Name = "${var.project_name}-postgres-subnet"
  }
}

resource "aws_security_group" "postgres" {
  name        = "${var.project_name}-postgres-sg"
  description = "Security group for PostgreSQL"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
    description = "PostgreSQL from VPC"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-postgres-sg"
  }
}

resource "aws_db_instance" "postgres" {
  identifier = "${var.project_name}-db"

  engine               = "postgres"
  engine_version       = var.postgres_version
  instance_class       = var.postgres_instance_class
  allocated_storage    = var.postgres_allocated_storage
  storage_encrypted    = true
  storage_type         = "gp3"

  db_name  = var.postgres_database
  username = var.postgres_username
  password = var.postgres_password  # Use AWS Secrets Manager in production

  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  vpc_security_group_ids = [aws_security_group.postgres.id]

  multi_az               = var.environment == "production" ? true : false
  backup_retention_period = var.postgres_backup_retention
  backup_window          = "03:00-04:00"
  maintenance_window     = "mon:04:00-mon:05:00"

  skip_final_snapshot       = var.environment != "production"
  final_snapshot_identifier = var.environment == "production" ? "${var.project_name}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  tags = {
    Name = "${var.project_name}-postgres"
  }
}

# ElastiCache Redis
resource "aws_elasticache_subnet_group" "redis" {
  name       = "${var.project_name}-redis-subnet"
  subnet_ids = module.vpc.private_subnets

  tags = {
    Name = "${var.project_name}-redis-subnet"
  }
}

resource "aws_security_group" "redis" {
  name        = "${var.project_name}-redis-sg"
  description = "Security group for Redis"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
    description = "Redis from VPC"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-redis-sg"
  }
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "${var.project_name}-redis"
  replication_group_description = "Redis cluster for embeddings cache"

  engine               = "redis"
  engine_version       = var.redis_version
  node_type            = var.redis_node_type
  num_cache_clusters   = var.environment == "production" ? 2 : 1
  port                 = 6379

  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [aws_security_group.redis.id]

  automatic_failover_enabled = var.environment == "production" ? true : false
  multi_az_enabled          = var.environment == "production" ? true : false

  parameter_group_name = "default.redis7"

  snapshot_retention_limit = var.environment == "production" ? 5 : 0
  snapshot_window         = "03:00-05:00"
  maintenance_window      = "sun:05:00-sun:07:00"

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  tags = {
    Name = "${var.project_name}-redis"
  }
}

# S3 Bucket for data lake
resource "aws_s3_bucket" "data_lake" {
  bucket = "${var.project_name}-data-${var.environment}"

  tags = {
    Name = "${var.project_name}-data-lake"
  }
}

resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "transition-to-intelligent-tiering"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "INTELLIGENT_TIERING"
    }
  }

  rule {
    id     = "expire-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

resource "aws_s3_bucket_public_access_block" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ECR Repositories
resource "aws_ecr_repository" "repositories" {
  for_each = toset(["backend-api", "ml-engine", "frontend", "data-pipeline", "deployer"])

  name                 = "${var.project_name}/${each.key}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name = "${var.project_name}-${each.key}"
  }
}

resource "aws_ecr_lifecycle_policy" "repositories" {
  for_each = aws_ecr_repository.repositories

  repository = each.value.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus     = "any"
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
