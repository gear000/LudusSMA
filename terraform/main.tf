terraform {
  required_version = ">= 1.9.0"
  backend "s3" {}
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
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

data "aws_iam_policy_document" "lambda_rotate_tokens_role_document" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_rotate_tokens_role" {
  name               = "LudusSMALambdaRotateTokensRole"
  assume_role_policy = data.aws_iam_policy_document.lambda_rotate_tokens_role_document.json
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
      "s3:DeleteObject"
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
      "arn:aws:scheduler:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*",
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
  statement {
    effect = "Allow"
    actions = [
      "transcribe:*"
    ]
    resources = [
      "*"
    ]
  }
}

resource "aws_iam_role_policy" "lambda_policy" {
  name   = "LudusSMALambdaPolicy"
  role   = aws_iam_role.lambda_role.id
  policy = data.aws_iam_policy_document.lambda_policy_document.json
}

data "aws_iam_policy_document" "lambda_rotate_tokens_policy_document" {
  statement {
    effect    = "Allow"
    actions   = ["logs:*"]
    resources = ["*"]
  }
  statement {
    effect = "Allow"
    actions = [
      "ssm:PutParameter"
    ]
    resources = [
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter${var.telegram_header_webhook_token_key_parameter}",
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter${var.meta_access_token_key_parameter}"
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "ssm:GetParameter",
    ]
    resources = [
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/telegram/*",
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/meta/*"
    ]
  }
}

resource "aws_iam_role_policy" "lambda_rotate_tokens_policy" {
  name   = "LudusSMALambdaRotateTokensPolicy"
  role   = aws_iam_role.lambda_rotate_tokens_role.id
  policy = data.aws_iam_policy_document.lambda_rotate_tokens_policy_document.json
}

data "aws_iam_policy_document" "scheduler_policy_document" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.events_sqs_queue.arn]
  }
  statement {
    effect = "Allow"
    actions = [
      "lambda:InvokeFunction"
    ]
    resources = [
      module.lambda_rotate_tokens.lambda_function_arn
    ]
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

# ### SQS QUEUE ###

resource "aws_sqs_queue" "events_sqs_queue" {
  name                       = "ScheduledEvents"
  visibility_timeout_seconds = 60
}

resource "aws_sqs_queue" "telegram_updates_sqs_queue" {
  name                        = "${var.sqs_telegram_updates_name}.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
  fifo_throughput_limit       = "perMessageGroupId"
  deduplication_scope         = "messageGroup"
  visibility_timeout_seconds  = 60

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

# ### SNS TOPIC ###

resource "aws_sns_topic" "error_sns_topic" {
  name         = "error-notification"
  display_name = "Error Notification"
}

resource "aws_sns_topic_subscription" "error_sns_subscription" {
  for_each = var.developers_email

  topic_arn = aws_sns_topic.error_sns_topic.arn
  protocol  = "email"
  endpoint  = each.value

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

module "lambda_auth_tg_requests" {
  source             = "./modules/lambda_function"
  lambda_name        = "auth-tg-requests"
  lambda_folder      = "../lambda_auth_tg_requests"
  lambda_handler     = "main.lambda_handler"
  lambda_memory_size = 256
  lambda_timeout     = 60
  lambda_runtime     = "python3.12"
  s3_bucket          = var.s3_bucket_artifact
  iam_role_arn       = aws_iam_role.lambda_role.arn
  environment_variables = {
    TELEGRAM_HEADER_WEBHOOK_TOKEN   = var.telegram_header_webhook_token_key_parameter
    SQS_QUEUE_TELEGRAM_UPDATES_NAME = aws_sqs_queue.telegram_updates_sqs_queue.name
    S3_BUCKET_CHAT_PERSISTENCE_NAME = aws_s3_bucket.chat_persistence_bucket.bucket
  }
  lambda_layers = [aws_lambda_layer_version.utils_layer.arn]
}

resource "aws_lambda_function_url" "auth_tg_http_trigger" {
  function_name      = module.lambda_auth_tg_requests.lambda_function_arn
  authorization_type = "NONE"
}

module "lambda_telegram_bot" {
  source             = "./modules/lambda_function"
  lambda_name        = "telegram-bot"
  lambda_folder      = "../lambda_telegram_bot"
  lambda_handler     = "main.lambda_handler"
  lambda_memory_size = 512
  lambda_timeout     = 60
  lambda_runtime     = "python3.12"
  s3_bucket          = var.s3_bucket_artifact
  iam_role_arn       = aws_iam_role.lambda_role.arn
  environment_variables = {
    TELEGRAM_BOT_KEY                  = var.telegram_bot_key_parameter
    TELEGRAM_ALLOW_CHAT_IDS           = var.telegram_allow_chat_ids_key_parameter
    SQS_QUEUE_TELEGRAM_UPDATES_NAME   = aws_sqs_queue.telegram_updates_sqs_queue.name
    SQS_QUEUE_EVENTS_ARN              = aws_sqs_queue.events_sqs_queue.arn
    IAM_ROLE_EVENT_SCHEDULER_ARN      = aws_iam_role.scheduler_role.arn
    S3_BUCKET_IMAGES_NAME             = aws_s3_bucket.images_bucket.bucket
    S3_BUCKET_CHAT_PERSISTENCE_NAME   = aws_s3_bucket.chat_persistence_bucket.bucket
    TRANSCRIBE_CUSTOM_VOCABULARY_NAME = aws_transcribe_vocabulary.custom_vocabulary.id
  }
  lambda_layers = [aws_lambda_layer_version.utils_layer.arn]
}

resource "aws_lambda_event_source_mapping" "telegram_bot_sqs_trigger" {
  event_source_arn = aws_sqs_queue.telegram_updates_sqs_queue.arn
  function_name    = module.lambda_telegram_bot.lambda_function_arn
  enabled          = true
  batch_size       = 1
}

module "lambda_create_ig_stories" {
  source             = "./modules/lambda_function"
  lambda_name        = "create-ig-stories"
  lambda_folder      = "../lambda_create_ig_stories"
  lambda_handler     = "main.lambda_handler"
  lambda_memory_size = 256
  lambda_timeout     = 60
  lambda_runtime     = "python3.12"
  s3_bucket          = var.s3_bucket_artifact
  iam_role_arn       = aws_iam_role.lambda_role.arn
  environment_variables = {
    META_CLIENT_SECRET = var.meta_client_secret_key_parameter
    META_ACCESS_TOKEN  = var.meta_access_token_key_parameter
  }
  lambda_layers = [aws_lambda_layer_version.utils_layer.arn]
}

resource "aws_lambda_event_source_mapping" "create_ig_stories_sqs_trigger" {
  event_source_arn                   = aws_sqs_queue.events_sqs_queue.arn
  function_name                      = module.lambda_create_ig_stories.lambda_function_arn
  enabled                            = true
  batch_size                         = 1
  maximum_batching_window_in_seconds = 300
}

module "lambda_rotate_tokens" {
  source             = "./modules/lambda_function"
  lambda_name        = "rotate_tokens"
  lambda_folder      = "../lambda_rotate_tokens"
  lambda_handler     = "main.lambda_handler"
  lambda_memory_size = 256
  lambda_timeout     = 60
  lambda_runtime     = "python3.12"
  s3_bucket          = var.s3_bucket_artifact
  iam_role_arn       = aws_iam_role.lambda_rotate_tokens_role.arn
  environment_variables = {
    TELEGRAM_BOT_KEY              = var.telegram_bot_key_parameter
    TELEGRAM_HEADER_WEBHOOK_TOKEN = var.telegram_header_webhook_token_key_parameter
    TELEGRAM_BOT_WEBHOOK_URL      = aws_lambda_function_url.auth_tg_http_trigger.function_url
  }
  lambda_layers = [aws_lambda_layer_version.utils_layer.arn]
}

### LAMBDA TRIGGER PERMISSIONS ###

resource "aws_lambda_permission" "tg_bot_permission_trigger" {
  statement_id  = "AllowSQSTrigger"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_telegram_bot.lambda_function_arn
  principal     = "sqs.amazonaws.com"
  source_arn    = aws_sqs_queue.telegram_updates_sqs_queue.arn
}

resource "aws_lambda_permission" "create_ig_stories_permission_trigger" {
  statement_id  = "AllowSQSTrigger"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_create_ig_stories.lambda_function_arn
  principal     = "sqs.amazonaws.com"
  source_arn    = aws_sqs_queue.events_sqs_queue.arn
}

# ### LAMBDA LAYER ###

resource "aws_lambda_layer_version" "utils_layer" {
  filename            = "../utils.zip"
  layer_name          = "LudusSMAUtilsLayer"
  compatible_runtimes = ["python3.12"]
  source_code_hash    = sha256(filebase64sha256("../utils.zip"))
}

### SCHEDULER ###

resource "aws_scheduler_schedule" "example" {
  name = "RotateTokensSchedule"

  flexible_time_window {
    mode                      = "FLEXIBLE"
    maximum_window_in_minutes = "15"
  }

  schedule_expression = "rate(50 days)"

  target {
    arn      = module.lambda_rotate_tokens.lambda_function_arn
    role_arn = aws_iam_role.scheduler_role.arn
    input    = jsonencode({})
  }
}

### TRANSCRIBE VOCABULARY ###

resource "aws_s3_object" "vocabulary_artifact" {
  bucket      = var.s3_bucket_artifact
  key         = "transcribe/${var.custom_vocabulary_file_name}"
  source      = "../${var.custom_vocabulary_file_name}"
  source_hash = sha256(filebase64sha256("../${var.custom_vocabulary_file_name}"))
}

resource "aws_transcribe_vocabulary" "custom_vocabulary" {
  vocabulary_name     = "ludussma-vocabulary"
  language_code       = "it-IT"
  vocabulary_file_uri = "s3://${aws_s3_object.vocabulary_artifact.bucket}/${aws_s3_object.vocabulary_artifact.key}"
}
