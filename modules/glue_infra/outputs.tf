output "glue_job_arn" {
  value = aws_glue_job.main.arn
}

output "sns_topic_arn" {
  value = aws_sns_topic.alerts.arn
}

output "code_bucket_name" {
  value = aws_s3_bucket.code_bucket.bucket
}