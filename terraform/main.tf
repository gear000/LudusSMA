terraform {
  required_version = ">= 1.9.0"
  backend "s3" {}
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

### LOG GROUP ###

resource "aws_cloudwatch_log_group" "log_group_api_gateway" {
  name              = "/aws/apigateway/${aws_apigatewayv2_api.lambda_api_gateway.name}"
  retention_in_days = 7
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

### API GATEWAY ###

# resource "aws_apigatewayv2_api" "lambda_api_gateway" {
#   name          = "ludussma-api-gateway"
#   protocol_type = "HTTP"
# }

# resource "aws_apigatewayv2_stage" "lambda_api_gateway_stage" {
#   api_id      = aws_apigatewayv2_api.lambda_api_gateway.id
#   name        = "prd"
#   auto_deploy = true

#   access_log_settings {
#     destination_arn = aws_cloudwatch_log_group.log_group_api_gateway.arn

#     format = jsonencode({
#       requestId               = "$context.requestId"
#       sourceIp                = "$context.identity.sourceIp"
#       requestTime             = "$context.requestTime"
#       protocol                = "$context.protocol"
#       httpMethod              = "$context.httpMethod"
#       resourcePath            = "$context.resourcePath"
#       routeKey                = "$context.routeKey"
#       status                  = "$context.status"
#       responseLength          = "$context.responseLength"
#       integrationErrorMessage = "$context.integrationErrorMessage"
#       }
#     )
#   }
# }

# resource "aws_apigatewayv2_integration" "lambda_api_gateway_integration" {
#   api_id             = aws_apigatewayv2_api.lambda_api_gateway.id
#   integration_type   = "AWS_PROXY"
#   integration_method = "POST"
#   integration_uri    = module.lambda_telegram_bot.lambda_function_arn
# }

# resource "aws_apigatewayv2_route" "get_lambda_api_gateway_route" {
#   api_id = aws_apigatewayv2_api.lambda_api_gateway.id

#   route_key = "POST /telegram-bot"
#   target    = "integrations/${aws_apigatewayv2_integration.lambda_api_gateway_integration.id}"
# }

### LAMBDA FUNCTIONS ###

module "lambda_auth_tg_requests" {
  source             = "./modules/lambda_function"
  lambda_name        = "auth-tg-requests"
  lambda_folder      = "../lambda_auth_tg_requests"
  lambda_handler     = "main.lambda_handler"
  lambda_memory_size = 256
  lambda_timeout     = 60
  lambda_runtime     = "python3.11"
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
  lambda_runtime     = "python3.11"
  s3_bucket          = var.s3_bucket_artifact
  iam_role_arn       = aws_iam_role.lambda_role.arn
  environment_variables = {
    TELEGRAM_BOT_KEY                = var.telegram_bot_key_parameter
    TELEGRAM_ALLOW_CHAT_IDS_KEY     = var.telegram_allow_chat_ids_key_parameter
    SQS_QUEUE_EVENTS_NAME           = aws_sqs_queue.events_sqs_queue.name
    S3_BUCKET_CHAT_PERSISTENCE_NAME = aws_s3_bucket.chat_persistence_bucket.bucket
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
  lambda_runtime     = "python3.11"
  s3_bucket          = var.s3_bucket_artifact
  iam_role_arn       = aws_iam_role.lambda_role.arn
  environment_variables = {
    S3_BUCKET_IMAGES_NAME           = aws_s3_bucket.images_bucket.bucket
    S3_BUCKET_CHAT_PERSISTENCE_NAME = aws_s3_bucket.chat_persistence_bucket.bucket
    SQS_QUEUE_TELEGRAM_UPDATES_NAME = aws_sqs_queue.telegram_updates_sqs_queue.name
  }
  lambda_layers = [aws_lambda_layer_version.utils_layer.arn]
}

resource "aws_lambda_event_source_mapping" "create_ig_stories_sqs_trigger" {
  event_source_arn = aws_sqs_queue.events_sqs_queue.arn
  function_name    = module.lambda_create_ig_stories.lambda_function_arn
  enabled          = true
  batch_size       = 1
}

### LAMBDA TRIGGER PERMISSIONS ###

# resource "aws_lambda_permission" "auth_tg_permission_trigger" {
#   statement_id  = "AllowAPIGatewayInvoke"
#   action        = "lambda:InvokeFunction"
#   function_name = module.lambda_auth_tg_requests.lambda_function_arn
#   principal     = "apigateway.amazonaws.com"
#   source_arn    = aws_apigatewayv2_api.lambda_api_gateway.arn
# }

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
  compatible_runtimes = ["python3.11"]
  source_code_hash    = sha256(filebase64sha256("../utils.zip"))
}
