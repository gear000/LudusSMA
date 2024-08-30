terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.64"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_codestarconnections_connection" "example" {
  name          = "test-connection"
  provider_type = "GitHub"
}
