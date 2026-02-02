#!/bin/bash
# LocalStack initialization script - creates S3 bucket

echo "Creating S3 bucket..."
awslocal s3 mb s3://project-management-files
awslocal s3api put-bucket-cors --bucket project-management-files --cors-configuration '{
  "CORSRules": [
    {
      "AllowedOrigins": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
      "AllowedHeaders": ["*"],
      "MaxAgeSeconds": 3000
    }
  ]
}'
echo "S3 bucket created successfully!"
