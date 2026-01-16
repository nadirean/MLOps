#!/bin/sh
set -e

awslocal s3 mb s3://airflow-xcom || true