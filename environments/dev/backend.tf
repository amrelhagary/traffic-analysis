terraform {
  backend "s3" {
    bucket         = "acs-dev-tf-state-bucket"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
