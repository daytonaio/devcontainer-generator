import os
import logging
from openai import AzureOpenAI
import instructor

def setup_azure_openai():
    logging.info("Setting up Azure OpenAI client...")
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )

def setup_instructor(openai_client):
    logging.info("Setting up Instructor client...")
    return instructor.patch(openai_client)

def check_env_vars():
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_API_VERSION",
        "MODEL",
        "GITHUB_TOKEN",
    ]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        print(
            f"Missing environment variables: {', '.join(missing_vars)}. "
            "Please configure the env vars file properly."
        )
        return False
    return True