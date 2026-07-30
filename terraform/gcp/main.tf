# Équivalent GKE du module EKS (terraform/aws/main.tf), pour démontrer
# la portabilité de l'architecture entre clouds.
#
# NOTE HONNÊTE (à garder en tête pour l'entretien) : ce fichier suit la
# même structure que le module AWS testé, mais n'a pas été déployé faute
# de compte GCP facturable disponible. À valider avec `terraform plan`
# avant tout déploiement réel.

terraform {
  required_providers {
    google = { source = "hashicorp/google", version = "~> 5.0" }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_container_cluster" "finagent" {
  name     = "finagent-cluster"
  location = var.region

  remove_default_node_pool = true
  initial_node_count       = 1
}

resource "google_container_node_pool" "finagent_nodes" {
  name       = "finagent-nodes"
  cluster    = google_container_cluster.finagent.name
  location   = var.region
  node_count = 2

  node_config {
    machine_type = "e2-medium"
  }
}

variable "project_id" { type = string }
variable "region" { default = "europe-west1" }
