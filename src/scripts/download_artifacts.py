import boto3
from settings import get_settings


def main():
    settings = get_settings()
    bucket = boto3.resource("s3").Bucket(settings.s3_bucket)  # type: ignore
    base_dir = settings.local_model_dir
    base_dir.mkdir(parents=True, exist_ok=True)

    for obj in bucket.objects.all():
        key = obj.key
        if key.endswith("/"):
            continue

        dest = base_dir / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        bucket.download_file(key, str(dest))
        print(f"Downloaded {key} to {dest}")


if __name__ == "__main__":
    main()
