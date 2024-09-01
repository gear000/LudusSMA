output "lambda_function_name" {
  description = "The name of the Lambda function"
  value       = aws_lambda_function.this.function_name
}

output "lambda_function_arn" {
  description = "The ARN of the Lambda function"
  value       = aws_lambda_function.this.arn
}

output "lambda_invoke_arn" {
  description = "The ARN to be used to invoke the Lambda function"
  value       = aws_lambda_function.this.invoke_arn
}
