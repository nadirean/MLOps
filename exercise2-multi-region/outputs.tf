output "bucket_arns" {
  value = {
    "${var.regions[0]}" = aws_s3_bucket.s3_us_east_1.arn,
    "${var.regions[1]}" = aws_s3_bucket.s3_us_west_2.arn,
  }
  description = "ARNs of the created buckets keyed by region"
}

output "bucket_regions" {
  value = {
    "${aws_s3_bucket.s3_us_east_1.id}" = var.regions[0],
    "${aws_s3_bucket.s3_us_west_2.id}" = var.regions[1],
  }
  description = "Bucket IDs mapped to regions"
}

output "replication_enabled" {
  value       = { for r in var.regions : r => var.enable_replication }
  description = "Replication status flag per region (configurable input for this exercise)"
}
