terraform {
  required_version = ">= 1.9.0"
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

resource "aws_s3_bucket" "s3_bucket_artifact" {
  bucket = "ludussma-artifact-v2"
}

resource "aws_dynamodb_table" "table_tf_plan_lock" {
  name                        = "ludussma-tf-plan-lock"
  billing_mode                = "PAY_PER_REQUEST"
  hash_key                    = "LockID"
  deletion_protection_enabled = true
  attribute {
    name = "LockID"
    type = "S"
  }
}

resource "aws_codestarconnections_connection" "github_connection" {
  name          = "ludussma-github-connection"
  provider_type = "GitHub"
}

### PARAMETERS ###

resource "aws_ssm_parameter" "secure_string" {
  for_each = local.parameters

  name  = each.key
  type  = "SecureString"
  value = each.value

  tags = var.tags
}

### CODEBUILD ###

resource "aws_cloudwatch_log_group" "log_group_codebuild_build" {
  name = "/aws/codebuild/LudusSMA-codebuild-tf-build"
}

data "aws_iam_policy_document" "assume_role_policy_codebuild" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["codebuild.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "codebuild_role" {
  name               = "ludussma-codebuild-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role_policy_codebuild.json
}

data "aws_iam_policy_document" "codebuild_policy_document" {

  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = [
      aws_cloudwatch_log_group.log_group_codebuild_build.arn,
      "${aws_cloudwatch_log_group.log_group_codebuild_build.arn}:*",
    ]
  }

  statement {
    effect  = "Allow"
    actions = ["*"]
    resources = [
      "arn:aws:s3:::*",
      "arn:aws:sns:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*",
      "arn:aws:sqs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*",
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*",
      "arn:aws:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*",
      "arn:aws:apigateway:${data.aws_region.current.name}::/*",
      "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*",
      "arn:aws:bedrock:us-west-2::*",
      "arn:aws:pipes:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*",
      "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/*",
      "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/*",
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "lambda:CreateEventSourceMapping",
      "logs:CreateLogDelivery"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "codebuild_policy" {
  name = "ludussma-codebuild-policy"
  role = aws_iam_role.codebuild_role.id

  policy = data.aws_iam_policy_document.codebuild_policy_document.json
}

resource "aws_codebuild_source_credential" "example" {
  auth_type   = "CODECONNECTIONS"
  server_type = "GITHUB"
  token       = aws_codestarconnections_connection.github_connection.arn
}

resource "aws_codebuild_project" "codebuild_tf_build" {

  name                   = "LudusSMA-codebuild-tf-build"
  service_role           = aws_iam_role.codebuild_role.arn
  concurrent_build_limit = 1
  tags                   = var.tags

  artifacts {
    type = "CODEPIPELINE"
  }

  environment {
    compute_type = "BUILD_GENERAL1_SMALL"
    image        = "hashicorp/terraform:latest"
    type         = "LINUX_CONTAINER"
    environment_variable {
      name  = "S3_BUCKET_ARTIFACT_NAME"
      value = aws_s3_bucket.s3_bucket_artifact.bucket
    }
    environment_variable {
      name  = "S3_BUCKET_ARTIFACT_KEY"
      value = "terraform/state/terraform.tfstate"
    }
    environment_variable {
      name  = "DYNAMODB_TABLE_NAME"
      value = aws_dynamodb_table.table_tf_plan_lock.name
    }
    environment_variable {
      name  = "AWS_REGION"
      value = var.aws_region
    }
  }

  logs_config {
    cloudwatch_logs {
      status     = "ENABLED"
      group_name = aws_cloudwatch_log_group.log_group_codebuild_build.name
    }
  }

  source {
    type      = "CODEPIPELINE"
    buildspec = "tf_foundation/buildspec.yml"
  }

}

### CODEPIPELINE ###

data "aws_iam_policy_document" "assume_role_policy_codepipeline" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["codepipeline.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "codepipeline_role" {
  name               = "ludussma-codepipeline-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role_policy_codepipeline.json
}

data "aws_iam_policy_document" "codepipeline_policy_document" {

  statement {
    effect = "Allow"

    actions = [
      "codestar-connections:UseConnection",
      "codeconnections:UseConnection"
    ]

    resources = ["*"]
  }

  statement {
    effect = "Allow"

    actions = [
      "codebuild:BatchGetBuilds",
      "codebuild:StartBuild",
      "codebuild:BatchGetBuildBatches",
      "codebuild:StartBuildBatch"
    ]

    resources = ["*"]
  }

  statement {
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:GetObjectVersion",
      "s3:PutObjectAcl",
      "s3:PutObject"
    ]

    resources = [
      aws_s3_bucket.s3_bucket_artifact.arn,
      "${aws_s3_bucket.s3_bucket_artifact.arn}/*"
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "servicecatalog:ListProvisioningArtifacts",
      "servicecatalog:CreateProvisioningArtifact",
      "servicecatalog:DescribeProvisioningArtifact",
      "servicecatalog:DeleteProvisioningArtifact",
      "servicecatalog:UpdateProduct"
    ]

    resources = ["*"]
  }

  statement {
    effect = "Allow"

    actions = [
      "ecr:DescribeImages"
    ]

    resources = ["*"]
  }

}

resource "aws_iam_role_policy" "codepipeline_policy" {
  name   = "ludussma-codepipeline-policy"
  role   = aws_iam_role.codepipeline_role.id
  policy = data.aws_iam_policy_document.codepipeline_policy_document.json
}

resource "aws_codepipeline" "terraform_pipeline" {
  name           = "ludussma-tf-pipeline"
  role_arn       = aws_iam_role.codepipeline_role.arn
  tags           = var.tags
  pipeline_type  = "V2"
  execution_mode = "QUEUED"

  artifact_store {
    location = aws_s3_bucket.s3_bucket_artifact.bucket
    type     = "S3"
  }

  stage {
    name = "Source"
    action {
      name             = "Init"
      category         = "Source"
      owner            = "AWS"
      version          = "1"
      provider         = "CodeStarSourceConnection"
      namespace        = "SourceVariables"
      output_artifacts = ["source_output"]
      run_order        = 1

      configuration = {
        ConnectionArn    = aws_codestarconnections_connection.github_connection.arn
        FullRepositoryId = var.source_repository
        BranchName       = var.source_branch
      }
    }
  }

  stage {
    name = "BuildAndDeploy"

    action {
      name            = "Build"
      category        = "Build"
      owner           = "AWS"
      provider        = "CodeBuild"
      input_artifacts = ["source_output"]
      version         = "1"

      configuration = {
        ProjectName = aws_codebuild_project.codebuild_tf_build.name
      }
    }
  }
}
