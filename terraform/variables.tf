variable "aws_region" {
  type        = string
  default     = "eu-west-1"
  description = "AWS Region"
}

variable "s3_bucket_artifact" {
  type        = string
  description = "S3 bucket for storing artifact"
}

variable "telegram_bot_key_parameter" {
  type    = string
  default = "/telegram/bot-token"
}

variable "telegram_allow_chat_ids_key_parameter" {
  type    = string
  default = "/telegram/allow-chat-ids"
}

variable "telegram_header_webhook_token_key_parameter" {
  type    = string
  default = "/telegram/header-webhook-token"
}

variable "meta_client_secret_key_parameter" {
  type    = string
  default = "/meta/client-secret"
}

variable "meta_access_token_key_parameter" {
  type    = string
  default = "/meta/access-token"
}

variable "sqs_telegram_updates_name" {
  type    = string
  default = "TelegramUpdates"
}

variable "bedrock_models_region" {
  type    = string
  default = "us-west-2"
}

variable "developers_email" {
  type = set(string)
  default = [
    "d.franzoni.97@gmail.com"
  ]
  description = "Emails of the developers for error reporting"
}

variable "custom_vocabulary_file_name" {
  type        = string
  default     = "vocabulary.txt"
  description = "Path to the custom vocabulary file"
}
