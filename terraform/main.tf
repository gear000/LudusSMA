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

### IAM ROLES ###

data "aws_iam_policy_document" "lambda_role_document" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_role" {
  name               = "LudusSMALambdaRole"
  assume_role_policy = data.aws_iam_policy_document.lambda_role_document.json
}

data "aws_iam_policy_document" "scheduler_role_document" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "scheduler_role" {
  name = "LudusSMASchedulerRole"

  assume_role_policy = data.aws_iam_policy_document.scheduler_role_document.json
}

data "aws_iam_policy_document" "pipe_role_document" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["pipes.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "pipe_role" {
  name = "LudusSMAPipeRole"

  assume_role_policy = data.aws_iam_policy_document.pipe_role_document.json
}

### IAM POLICIES ###

data "aws_iam_policy_document" "lambda_policy_document" {
  statement {
    effect    = "Allow"
    actions   = ["logs:*"]
    resources = ["*"]
  }
  statement {
    effect  = "Allow"
    actions = ["ssm:GetParameter"]
    resources = [
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/telegram/*",
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/meta/*"
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes"
    ]
    resources = [
      aws_sqs_queue.events_sqs_queue.arn,
      aws_sqs_queue.telegram_updates_sqs_queue.arn
    ]
  }
  statement {
    effect  = "Allow"
    actions = ["sqs:SendMessage"]
    resources = [
      aws_sqs_queue.telegram_updates_sqs_queue.arn
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket",
      "s3:ListObject",
    ]
    resources = [
      aws_s3_bucket.chat_persistence_bucket.arn,
      "${aws_s3_bucket.chat_persistence_bucket.arn}/*",
      aws_s3_bucket.images_bucket.arn,
      "${aws_s3_bucket.images_bucket.arn}/*"
    ]
  }
  statement {
    effect  = "Allow"
    actions = ["*"]
    resources = [
      "arn:aws:scheduler:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:schedule/*",
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "iam:PassRole",
    ]
    resources = [
      aws_iam_role.scheduler_role.arn
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "bedrock:InvokeModel"
    ]
    resources = [
      "arn:aws:bedrock:${var.bedrock_models_region}::foundation-model/*"
    ]
  }
}

resource "aws_iam_role_policy" "lambda_policy" {
  name   = "LudusSMALambdaPolicy"
  role   = aws_iam_role.lambda_role.id
  policy = data.aws_iam_policy_document.lambda_policy_document.json
}

data "aws_iam_policy_document" "scheduler_policy_document" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.events_sqs_queue.arn]
  }
}

resource "aws_iam_role_policy" "scheduler_policy" {
  name   = "LudusSMASchedulerPolicy"
  role   = aws_iam_role.scheduler_role.id
  policy = data.aws_iam_policy_document.scheduler_policy_document.json
}

data "aws_iam_policy_document" "pipe_policy_document" {
  statement {
    effect = "Allow"
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
    ]
    resources = [
      aws_sqs_queue.telegram_updates_sqs_queue_ddl.arn,
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "sns:Publish",
    ]
    resources = [
      aws_sns_topic.error_sns_topic.arn
    ]
  }
}

resource "aws_iam_role_policy" "pipe_policy" {
  name   = "LudusSMAPipePolicy"
  role   = aws_iam_role.pipe_role.id
  policy = data.aws_iam_policy_document.pipe_policy_document.json
}

### S3 BUCKETS ###

resource "aws_s3_bucket" "images_bucket" {
  bucket = "ludussma-images"
}

resource "aws_s3_bucket" "chat_persistence_bucket" {
  bucket = "ludussma-chat-persistence"
}

### SQS QUEUE ###

resource "aws_sqs_queue" "events_sqs_queue" {
  name                       = "ScheduledEvents"
  visibility_timeout_seconds = 30
}

resource "aws_sqs_queue" "telegram_updates_sqs_queue" {
  name                        = "${var.sqs_telegram_updates_name}.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
  fifo_throughput_limit       = "perMessageGroupId"
  deduplication_scope         = "messageGroup"
  visibility_timeout_seconds  = 30

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.telegram_updates_sqs_queue_ddl.arn
    maxReceiveCount     = 1
  })
}

resource "aws_sqs_queue" "telegram_updates_sqs_queue_ddl" {
  name       = "${var.sqs_telegram_updates_name}DDL.fifo"
  fifo_queue = true

  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = ["arn:aws:sqs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${var.sqs_telegram_updates_name}.fifo"]
  })
}

### SNS TOPIC ###

resource "aws_sns_topic" "error_sns_topic" {
  name         = "error-notification"
  display_name = "Error Notification"
}

resource "aws_sns_topic_subscription" "error_sns_subscription" {
  topic_arn = aws_sns_topic.error_sns_topic.arn
  protocol  = "email"
  endpoint  = "d.franzoni.97@gmail.com"
}

### EVENTBRIDGE PIPES ###

resource "aws_pipes_pipe" "pipe_error_notification" {
  name          = "error-notification"
  role_arn      = aws_iam_role.pipe_role.arn
  source        = aws_sqs_queue.telegram_updates_sqs_queue_ddl.arn
  target        = aws_sns_topic.error_sns_topic.arn
  desired_state = "RUNNING"

  target_parameters {
    input_template = jsonencode({
      body           = "<$.body>"
      eventSourceARN = "<$.eventSourceARN>"
    })
  }
}

### LAMBDA FUNCTIONS ###

resource "null_resource" "auth_tg_requests_deps" {
  triggers = {
    refresh = sha256(filesha256("../lambda_auth_tg_requests/requirements.txt"))
  }
  provisioner "local-exec" {
    command = "pip install -r ../lambda_auth_tg_requests/requirements.txt --target ../lambda_auth_tg_requests"
  }
}

data "archive_file" "auth_tg_zip" {
  type        = "zip"
  source_dir  = "../lambda_auth_tg_requests"
  output_path = "auth_tg_requests.zip"

  depends_on = [null_resource.auth_tg_requests_deps]
}

resource "aws_lambda_function" "auth_tg_requests_function" {
  function_name    = "auth-tg-requests"
  source_code_hash = data.archive_file.auth_tg_zip.output_base64sha256
  handler          = "main.lambda_handler"
  runtime          = "python3.11"
  memory_size      = 256
  timeout          = 60
  role             = aws_iam_role.lambda_role.arn

  environment {
    variables = {
      TELEGRAM_HEADER_WEBHOOK_TOKEN   = var.telegram_header_webhook_token_key_parameter
      SQS_QUEUE_TELEGRAM_UPDATES_NAME = aws_sqs_queue.telegram_updates_sqs_queue.name
      S3_BUCKET_CHAT_PERSISTENCE_NAME = aws_s3_bucket.chat_persistence_bucket.bucket
    }
  }

  filename = data.archive_file.auth_tg_zip.output_path

  architectures = ["x86_64"]
  layers        = [aws_lambda_layer_version.utils_layer.arn]
}

resource "null_resource" "telegram_bot_deps" {
  triggers = {
    refresh = sha256(filesha256("../lambda_telegram_bot/requirements.txt"))
  }
  provisioner "local-exec" {
    command = "pip install -r ../lambda_telegram_bot/requirements.txt --target ../lambda_telegram_bot"
  }
}

data "archive_file" "telegram_bot_zip" {
  type        = "zip"
  source_dir  = "../lambda_telegram_bot"
  output_path = "telegram_bot.zip"

  depends_on = [null_resource.telegram_bot_deps]
}

resource "aws_lambda_function" "telegram_bot_function" {
  function_name    = "telegram-bot"
  source_code_hash = data.archive_file.telegram_bot_zip.output_base64sha256
  handler          = "main.lambda_handler"
  runtime          = "python3.11"
  memory_size      = 256
  timeout          = 60
  role             = aws_iam_role.lambda_role.arn

  environment {
    variables = {
      TELEGRAM_BOT_KEY                = var.telegram_bot_key_parameter
      TELEGRAM_ALLOW_CHAT_IDS_KEY     = var.telegram_allow_chat_ids_key_parameter
      SQS_QUEUE_EVENTS_NAME           = aws_sqs_queue.events_sqs_queue.name
      S3_BUCKET_CHAT_PERSISTENCE_NAME = aws_s3_bucket.chat_persistence_bucket.bucket
    }
  }

  filename = data.archive_file.telegram_bot_zip.output_path

  architectures = ["x86_64"]
  layers        = [aws_lambda_layer_version.utils_layer.arn]
}

resource "null_resource" "create_ig_stories_deps" {
  triggers = {
    refresh = sha256(filesha256("../lambda_create_ig_stories/requirements.txt"))
  }
  provisioner "local-exec" {
    command = "pip install -r ../lambda_create_ig_stories/requirements.txt --target ../lambda_create_ig_stories"
  }
}

data "archive_file" "create_ig_stories_zip" {
  type        = "zip"
  source_dir  = "../lambda_create_ig_stories"
  output_path = "create_ig_stories.zip"

  depends_on = [null_resource.create_ig_stories_deps]
}

resource "aws_lambda_function" "random_images_function" {
  function_name    = "random-images"
  source_code_hash = data.archive_file.create_ig_stories_zip.output_base64sha256
  handler          = "main.lambda_handler"
  runtime          = "python3.11"
  memory_size      = 256
  timeout          = 60
  role             = aws_iam_role.lambda_role.arn

  environment {
    variables = {
      S3_BUCKET_IMAGES_NAME           = aws_s3_bucket.images_bucket.bucket
      S3_BUCKET_CHAT_PERSISTENCE_NAME = aws_s3_bucket.chat_persistence_bucket.bucket
      SQS_QUEUE_TELEGRAM_UPDATES_NAME = aws_sqs_queue.telegram_updates_sqs_queue.name
    }
  }

  filename = data.archive_file.create_ig_stories_zip.output_path

  architectures = ["x86_64"]
  layers        = [aws_lambda_layer_version.utils_layer.arn]
}

### LAMBDA LAYER ###

resource "aws_lambda_layer_version" "utils_layer" {
  filename            = "../utils.zip"
  layer_name          = "LudusSMAUtilsLayer"
  compatible_runtimes = ["python3.11"]
}

