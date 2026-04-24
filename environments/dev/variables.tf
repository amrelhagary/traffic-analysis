variable "environment" {
  description = "Environment name (dev or prod)"
  type        = string
}

variable "region" {
  description = "AWS Region"
  type        = string
  default     = "us-east-1"
}

variable "alert_email" {
  description = "Email address to receive SNS alerts"
  type        = string
}

variable "s3_input_path" {
  description = "S3 Input File path"
  type        = string
}

variable "s3_input_bucket" {
  description = "S3 Input Bucket"
  type        = string
}

variable "s3_output_path" {
  description = "S3 Output File path"
  type        = string
}

variable "s3_output_bucket" {
  description = "S3 Output Bucket"
  type        = string
}