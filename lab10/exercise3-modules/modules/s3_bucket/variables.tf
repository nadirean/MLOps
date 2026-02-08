variable "bucket_name_prefix" {
  description = "Prefix for the S3 bucket name"
  type        = string
}

variable "region" {
  description = "Region where the bucket will be created"
  type        = string
}

variable "random_suffix" {
  description = "Random hex suffix appended to the bucket name"
  type        = string
}

variable "lifecycle_days" {
  description = "Days before transitioning objects to colder storage"
  type        = number
  default     = 90
}

variable "lifecycle_storage_class" {
  description = "Target storage class for lifecycle transition"
  type        = string
  default     = "GLACIER"
}
