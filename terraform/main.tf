terraform {
  required_version = ">= 1.9.0"
  backend "local" {}
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

resource "aws_ssm_parameter" "test-params" {
  name  = "/test/test-params"
  type  = "String"
  value = "test-value"
}
