variable "aws_region" {
    type = string
    default = "eu-west-1"
    description = "AWS Region" 
}

variable "s3_bucket_artifact_name" {
    type = string
    default = "ludussma-artifact"
    description = "S3 Bucket for storage tf plan purposes" 
}