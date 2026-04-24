environment = "prod"
region      = "us-west-2" # Example different region
alert_email = "prod-alerts@example.com"

s3_input_path  = "s3://${module.glue_infra.code_bucket_name}/input/data.sql"
s3_output_path = "s3://${module.glue_infra.code_bucket_name}/output"
