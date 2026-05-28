terraform {
  required_version = ">= 1.10.0"

  backend "gcs" {
    bucket = "gorillac-terraform-state"
    prefix = "terraformProjects"
  }

  required_providers {
    google = {
      source = "hashicorp/google"
    }
    archive = {
      source = "hashicorp/archive"
    }
  }
}

# GCP Provider
provider "google" {
  project               = "gorillac-site"
  region                = "us-central1"
  user_project_override = true
  billing_project       = "gorillac-site"
}
