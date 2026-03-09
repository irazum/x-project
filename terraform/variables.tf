variable "aws_region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "project-management"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.small"
}

variable "ssh_public_key" {
  description = "SSH public key for EC2 access"
  type        = string
}

variable "allowed_ssh_cidrs" {
  description = "CIDR blocks allowed to SSH into the instance"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "s3_bucket_name" {
  description = "S3 bucket name for file storage"
  type        = string
  default     = "project-management-files"
}

# --- Lambda: Image Processor ---

variable "lambda_memory_size" {
  description = "Memory (MB) allocated to the image processor Lambda"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Timeout (seconds) for the image processor Lambda"
  type        = number
  default     = 30
}

variable "lambda_log_retention_days" {
  description = "CloudWatch log retention in days for the Lambda"
  type        = number
  default     = 14
}

variable "pillow_layer_zip_path" {
  description = "Path to the Pillow Lambda layer zip file"
  type        = string
  default     = "../lambdas/layers/pillow.zip"
}
