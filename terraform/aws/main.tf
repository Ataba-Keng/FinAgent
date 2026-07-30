# Cluster EKS minimal pour héberger FinAgent.
# Réutilise les acquis Terraform/AWS déjà en place sur le data lake existant
# (mêmes conventions de nommage, tags, remote state S3).

terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = var.aws_region
}

module "eks" {
  source          = "terraform-aws-modules/eks/aws"
  version         = "~> 20.0"
  cluster_name    = "finagent-cluster"
  cluster_version = "1.30"

  vpc_id     = var.vpc_id
  subnet_ids = var.subnet_ids

  eks_managed_node_groups = {
    finagent_nodes = {
      instance_types = ["t3.medium"]
      min_size       = 2
      max_size       = 4
      desired_size   = 2
    }
  }

  tags = {
    Project = "finagent"
    Env     = var.environment
  }
}

variable "aws_region" { default = "eu-west-3" }
variable "vpc_id" { type = string }
variable "subnet_ids" { type = list(string) }
variable "environment" { default = "portfolio" }

output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}
