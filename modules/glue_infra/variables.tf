variable "environment" {
  type = string
}

variable "region" {
  type = string
}

variable "job_name" {
  type = string
  default = "traffic-analysis"
}

variable "script_name" {
  type = string
  default = "glue.py"
}

variable "s3_input_path" {
  type = string
}

variable "s3_output_path" {
  type = string
}

variable "alert_email" {
  type = string
}
