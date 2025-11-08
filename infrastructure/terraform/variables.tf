variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "embeddings-saas"
}

# VPC Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b", "us-west-2c"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

# EKS Configuration
variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.28"
}

variable "general_node_instance_types" {
  description = "Instance types for general node group"
  type        = list(string)
  default     = ["t3.large"]
}

variable "general_node_min_size" {
  description = "Minimum size of general node group"
  type        = number
  default     = 2
}

variable "general_node_max_size" {
  description = "Maximum size of general node group"
  type        = number
  default     = 10
}

variable "general_node_desired_size" {
  description = "Desired size of general node group"
  type        = number
  default     = 3
}

variable "ml_node_instance_types" {
  description = "Instance types for ML node group"
  type        = list(string)
  default     = ["c5.2xlarge"]
}

variable "ml_node_min_size" {
  description = "Minimum size of ML node group"
  type        = number
  default     = 1
}

variable "ml_node_max_size" {
  description = "Maximum size of ML node group"
  type        = number
  default     = 5
}

variable "ml_node_desired_size" {
  description = "Desired size of ML node group"
  type        = number
  default     = 1
}

# RDS Configuration
variable "postgres_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "15.4"
}

variable "postgres_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "postgres_allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 100
}

variable "postgres_database" {
  description = "Database name"
  type        = string
  default     = "embeddings_saas"
}

variable "postgres_username" {
  description = "Master username"
  type        = string
  default     = "postgres"
  sensitive   = true
}

variable "postgres_password" {
  description = "Master password"
  type        = string
  sensitive   = true
}

variable "postgres_backup_retention" {
  description = "Backup retention period in days"
  type        = number
  default     = 7
}

# Redis Configuration
variable "redis_version" {
  description = "Redis version"
  type        = string
  default     = "7.0"
}

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.medium"
}
