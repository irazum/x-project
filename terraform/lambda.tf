# --- Lambda: Image Processor ---

# Package Lambda code into a zip (exclude requirements.txt — only needed at build time)
data "archive_file" "image_processor" {
  type        = "zip"
  source_dir  = "${path.module}/../lambdas/image_processor"
  excludes    = ["requirements.txt"]
  output_path = "${path.module}/.build/image_processor.zip"
}

# IAM role for Lambda execution
resource "aws_iam_role" "image_processor" {
  name = "${var.project_name}-image-processor-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-image-processor-role"
  }
}

# CloudWatch Logs policy — Lambda needs to write logs
resource "aws_iam_role_policy" "image_processor_logs" {
  name = "${var.project_name}-image-processor-logs"
  role = aws_iam_role.image_processor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "arn:aws:logs:${var.aws_region}:*:log-group:/aws/lambda/${var.project_name}-image-processor:*"
      }
    ]
  })
}

# S3 access policy — read from uploads/logos/, write to logos/
resource "aws_iam_role_policy" "image_processor_s3" {
  name = "${var.project_name}-image-processor-s3"
  role = aws_iam_role.image_processor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
        ]
        Resource = "${aws_s3_bucket.files.arn}/uploads/logos/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
        ]
        Resource = "${aws_s3_bucket.files.arn}/logos/*"
      }
    ]
  })
}

# Lambda layer for Pillow (heavy dependency — use a public layer)
resource "aws_lambda_layer_version" "pillow" {
  layer_name          = "${var.project_name}-pillow"
  description         = "Pillow image processing library"
  compatible_runtimes = ["python3.14"]

  filename         = var.pillow_layer_zip_path
  source_code_hash = filebase64sha256(var.pillow_layer_zip_path)
}

# Lambda function
resource "aws_lambda_function" "image_processor" {
  function_name = "${var.project_name}-image-processor"
  role          = aws_iam_role.image_processor.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.14"
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  filename         = data.archive_file.image_processor.output_path
  source_code_hash = data.archive_file.image_processor.output_base64sha256

  layers = [aws_lambda_layer_version.pillow.arn]

  environment {
    variables = {
      LOGO_MAX_WIDTH       = "800"
      LOGO_MAX_HEIGHT      = "800"
      LOGO_THUMBNAIL_SIZE  = "200"
      LOGO_UPLOAD_PREFIX   = "uploads/logos"
      LOGO_PROCESSED_PREFIX = "logos"
    }
  }

  tags = {
    Name = "${var.project_name}-image-processor"
  }
}

# CloudWatch Log Group (explicit to control retention)
resource "aws_cloudwatch_log_group" "image_processor" {
  name              = "/aws/lambda/${aws_lambda_function.image_processor.function_name}"
  retention_in_days = var.lambda_log_retention_days

  tags = {
    Name = "${var.project_name}-image-processor-logs"
  }
}

# Allow S3 to invoke the Lambda function
resource "aws_lambda_permission" "s3_invoke" {
  statement_id   = "AllowS3Invoke"
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.image_processor.function_name
  principal      = "s3.amazonaws.com"
  source_arn     = aws_s3_bucket.files.arn
  source_account = data.aws_caller_identity.current.account_id
}
