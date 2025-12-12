variable "regions" {
  type    = list(string)
  default = ["us-east-1", "us-west-2"]
}

variable "bucket_name_prefix" {
  type        = string
  description = "Prefix used for all S3 bucket names"
  default     = "multi-region-bucket"
}

variable "enable_replication" {
  type        = bool
  description = "Whether to enable replication settings (boolean flag only for this exercise)"
  default     = false
}

variable "glacier_transition_days" {
  type        = number
  description = "Days before transitioning objects to Glacier Instant Retrieval"
  default     = 90
}
