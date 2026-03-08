output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.app.id
}

output "public_ip" {
  description = "EC2 Elastic IP address (stable)"
  value       = aws_eip.app.public_ip
}

output "public_dns" {
  description = "EC2 public DNS"
  value       = aws_eip.app.public_dns
}

output "s3_bucket_name" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.files.id
}

output "ssh_command" {
  description = "SSH command to connect"
  value       = "ssh ubuntu@${aws_eip.app.public_ip}"
}
