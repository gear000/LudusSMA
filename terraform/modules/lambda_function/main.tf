resource "null_resource" "build_deps" {
  triggers = {
    always = uuid()
  }
  provisioner "local-exec" {
    command = "pip install -r ${var.lambda_folder}/requirements.txt --platform manylinux2014_x86_64 --target ${var.lambda_folder} --only-binary=:all:"
  }
}

data "archive_file" "create_zip" {
  type        = "zip"
  source_dir  = var.lambda_folder
  output_path = var.lambda_name

  depends_on = [null_resource.build_deps]
}

resource "aws_s3_object" "lambda_zip" {
  bucket      = var.s3_bucket
  key         = "lambda_package/${var.lambda_name}.zip"
  source      = data.archive_file.create_zip.output_path
  source_hash = data.archive_file.create_zip.output_base64sha256
}

resource "aws_lambda_function" "this" {
  function_name    = var.lambda_name
  source_code_hash = data.archive_file.create_zip.output_base64sha256
  s3_bucket        = aws_s3_object.lambda_zip.bucket
  s3_key           = aws_s3_object.lambda_zip.key
  memory_size      = var.lambda_memory_size
  timeout          = var.lambda_timeout
  handler          = var.lambda_handler
  runtime          = var.lambda_runtime
  role             = var.iam_role_arn
  architectures    = ["x86_64"]
  environment {
    variables = var.environment_variables
  }
  layers = var.lambda_layers
}
