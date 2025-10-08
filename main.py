import os
import argparse
from dotenv import load_dotenv
from settings import Settings
import yaml


def export_envs(environment: str = "dev") -> None:
    # Load secrets from secrets.yaml if it exists
    if os.path.exists("secrets.yaml"):
        with open("secrets.yaml", "r") as file:
            secrets = yaml.safe_load(file)
        for key, value in secrets.items():
            os.environ[key] = value

    # Load environment variables from the specified .env file
    env_file = f".env.{environment}"
    if os.path.exists(env_file):
        load_dotenv(env_file)
    else:
        raise FileNotFoundError(f"{env_file} does not exist.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Load environment variables from specified.env file."
    )
    parser.add_argument(
        "--environment",
        type=str,
        default="dev",
        help="The environment to load (dev, test, prod)",
    )
    args = parser.parse_args()

    export_envs(args.environment)

    settings = Settings()

    print("APP_NAME: ", settings.APP_NAME)
    print("ENVIRONMENT: ", settings.ENVIRONMENT)
    print("API_KEY: ", settings.API_KEY)
