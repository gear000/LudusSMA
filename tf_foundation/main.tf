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

### CODEBUILD ###

resource "aws_cloudwatch_log_group" "log_group_codebuild_build" {
  name = "/aws/codebuild/LudusSMA-codebuild-tf-build"
}

resource "aws_cloudwatch_log_group" "log_group_codebuild_deploy" {
  name = "/aws/codebuild/LudusSMA-codebuild-tf-deploy"
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
      aws_cloudwatch_log_group.log_group_codebuild_deploy.arn,
      "${aws_cloudwatch_log_group.log_group_codebuild_deploy.arn}:*"
    ]
  }

  statement {
    actions = ["*"]
    resources = [
      "arn:aws:s3:::*",
      "arn:aws:sqs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*",
      "arn:aws:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:function:*",
      "arn:aws:sns:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*",
      "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/*",
      "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/*",
      "arn:aws:pipes:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"
    ]
  }
}

resource "aws_iam_policy" "codebuild_policy" {
  name        = "ludussma-codebuild-policy"
  description = "Policy for CodeBuild"

  policy = data.aws_iam_policy_document.codebuild_policy_document.json
}


resource "aws_iam_role_policy_attachment" "codebuild_policy_attach" {
  role       = aws_iam_role.codebuild_role.name
  policy_arn = aws_iam_policy.codebuild_policy.arn
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
    buildspec = "tf_foundation/build_scripts/buildspec_tf_build.yml"
  }

}

resource "aws_codebuild_project" "codebuild_tf_deploy" {

  name                   = "LudusSMA-codebuild-tf-deploy"
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
      name  = "DDB_TABLE_NAME"
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
    buildspec = "tf_foundation/build_scripts/buildspec_tf_deploy.yml"
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

resource "aws_iam_policy" "codepipeline_policy" {
  name        = "ludussma-codepipeline-policy"
  description = "Policy for CodePipeline"
  policy      = data.aws_iam_policy_document.codepipeline_policy_document.json
}


resource "aws_iam_role_policy_attachment" "codepipeline_policy_attach" {
  role       = aws_iam_role.codepipeline_role.name
  policy_arn = aws_iam_policy.codepipeline_policy.arn
}

resource "aws_codepipeline" "terraform_pipeline" {
  name     = "ludussma-terraform-pipeline"
  role_arn = aws_iam_role.codepipeline_role.arn
  tags     = var.tags

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
        FullRepositoryId = "gear000/LudusSMA"
        BranchName       = "feat/tf_foundation"
      }
    }
  }

  stage {
    name = "Build"

    action {
      name             = "Build"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      input_artifacts  = ["source_output"]
      output_artifacts = ["build_output"]
      version          = "1"

      configuration = {
        ProjectName = aws_codebuild_project.codebuild_tf_build.name
      }
    }
  }

  stage {
    name = "Deploy"

    action {
      name             = "Deploy"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      input_artifacts  = ["build_output"]
      output_artifacts = ["deploy_output"]
      version          = "1"

      configuration = {
        ProjectName = aws_codebuild_project.codebuild_tf_deploy.name
      }
    }
  }
}
