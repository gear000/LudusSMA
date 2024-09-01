
variable "lambda_name" {
  description = "The name of the Lambda function"
  type        = string
}

variable "lambda_folder" {
  description = "Path to the folder containing Lambda function code"
  type        = string
}

variable "lambda_handler" {
  description = "The handler for the Lambda function"
  type        = string
}

variable "lambda_runtime" {
  description = "The runtime for the Lambda function"
  type        = string
}

variable "lambda_memory_size" {
  description = "The memory size for the Lambda function"
  type        = number
}

variable "lambda_timeout" {
  description = "The timeout for the Lambda function"
  type        = number
}

variable "s3_bucket" {
  description = "The S3 bucket to store Lambda package"
  type        = string
}

variable "iam_role_arn" {
  description = "IAM role ARN for Lambda function"
  type        = string
}

variable "environment_variables" {
  description = "Environment variables for the Lambda function"
  type        = map(string)
  default     = {}
}

variable "lambda_layers" {
  description = "List of Lambda layer ARNs to attach to the Lambda function"
  type        = list(string)
  default     = []
}
