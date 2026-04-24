provider "aws" {
  region  = var.region
  profile = "prod_account" # Ensure this profile exists in ~/.aws/credentials
}

module "glue_infra" {
  source = "../../modules/glue_infra"

  environment      = var.environment
  region           = var.region
  job_name         = "traffic-analysis-prod"
  script_name      = "glue.py"
  alert_email      = var.alert_email
  s3_input_path    = var.s3_input_path
  s3_output_path   = var.s3_output_path
}
