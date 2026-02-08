variable "regions" {
  type    = list(string)
  default = ["us-east-1", "us-west-2"]
}

variable "bucket_name_prefix" {
  type        = string
  description = "Prefix used for all S3 buckets"
  default     = "multi-region-bucket"
}
