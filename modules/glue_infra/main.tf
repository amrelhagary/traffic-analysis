resource "aws_s3_bucket" "code_bucket" {
  bucket = "acs-${var.environment}-glue-job-scripts"
  
  tags = {
    Name        = "${var.environment}-glue-scripts"
    Environment = var.environment
  }
}

resource "aws_s3_bucket" "logs_bucket" {
  bucket = "acs-${var.environment}-glue-logs"
  
  tags = {
    Name        = "${var.environment}-glue-logs"
    Environment = var.environment
  }
}

resource "aws_glue_job" "main" {
  name         = "acs-${var.environment}-${var.job_name}"
  role_arn     = aws_iam_role.glue_role.arn
  
  command {
    name         = "glueetl"
    script_location = "s3://${aws_s3_bucket.code_bucket.bucket}/${var.script_name}"
    python_version = "3"
  }

  glue_version  = "3.0"
  worker_type   = "G.1X"
  number_of_workers = 2
  
  # Glue Job Logging
  default_arguments = {
    "--S3_INPUT_FILE_PATH" = var.s3_input_path
    "--S3_OUTPUT_FILE_PATH" = var.s3_output_path
    "--enable-metrics" = "true"
    "--job-bookmark-option" = "job-bookmark-disable"
  }

  tags = {
    Environment = var.environment
    JobName     = var.job_name
  }
  depends_on = [aws_s3_object.script]
}

# Upload Python Script to S3
resource "aws_s3_object" "script" {
  bucket = aws_s3_bucket.code_bucket.bucket
  # key    = "${var.environment}/${var.script_name}"
  key    = "${var.script_name}"
  source = "../../scripts/glue.py"
  etag   = filemd5("../../scripts/glue.py")
}

# IAM Role for Glue
resource "aws_iam_role" "glue_role" {
  name = "${var.environment}-glue-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Environment = var.environment
  }
}

resource "aws_iam_role_policy" "glue_policy" {
  name = "${var.environment}-glue-policy"
  role = aws_iam_role.glue_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
          "s3:DeleteObject"
        ]
        Effect   = "Allow"
        Resource = [
          "arn:aws:s3:::${var.s3_input_bucket}",
          "arn:aws:s3:::${var.s3_output_bucket}",
          "arn:aws:s3:::${var.s3_input_bucket}/*",
          "arn:aws:s3:::${var.s3_output_bucket}/*",
          "arn:aws:s3:::${aws_s3_bucket.code_bucket.bucket}/*"
        ]
      },
      {
        Action   = "logs:CreateLogGroup"
        Effect   = "Allow"
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Effect = "Allow"
        Resource = "arn:aws:logs:*:*:log-group:/aws-glue/jobs/*"
      }
    ]
  })
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.environment}-glue-dashboard"
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title = "Glue Job Status"
          metrics = [
            ["AWS/Glue", "JobRunStartTime", "JobName", var.environment]
          ]
          region = var.region
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title = "Glue Job Duration"
          metrics = [
            ["AWS/Glue", "JobRunTime", "JobName", var.environment]
          ]
          region = var.region
        }
      }
    ]
  })
}

# SNS Topic for Alerting
resource "aws_sns_topic" "alerts" {
  name = "${var.environment}-glue-alerts"
}

resource "aws_cloudwatch_metric_alarm" "job_failed" {
  alarm_name          = "${var.environment}-glue-job-failed"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "JobRunStartTime"
  namespace           = "AWS/Glue"
  period              = 300
  statistic           = "Sum"
  threshold           = 0 
  alarm_description   = "This alarm triggers when a Glue job fails in ${var.environment}."
  
  dimensions = {
    JobName = var.environment
  }
  
  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn] # Optional: Notify on success
}

resource "aws_sns_topic_subscription" "email_alert" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}
