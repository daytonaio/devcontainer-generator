import os
import logging
from openai import AzureOpenAI
import instructor

def setup_azure_openai():
    logging.info("Setting up Azure OpenAI client...")

    # Retrieve environment variables for embedding model configuration
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    
    # Check if API key, endpoint, and version are set
    if not api_key or not endpoint or not api_version:
        logging.error("Azure OpenAI configuration missing. Check API key, endpoint, or version.")
        raise ValueError("Azure OpenAI configuration missing. Ensure AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_API_VERSION are set in environment variables.")
    
    # Initialize Azure OpenAI client
    openai_client = AzureOpenAI(
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version=api_version,
    )
    
    # Ensure the embeddings method is available
    if not hasattr(openai_client, 'embeddings'):
        logging.error("OpenAI client does not support embeddings. Please check API version.")
        raise ValueError("Azure OpenAI client does not support embeddings with the current API version.")

    return openai_client

def setup_instructor(openai_client):
    logging.info("Setting up Instructor client...")
    try:
        return instructor.patch(openai_client)
    except Exception as e:
        logging.error(f"Failed to initialize Instructor client: {e}")
        raise

def check_env_vars():
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_API_VERSION",
        "MODEL",
        "GITHUB_TOKEN",
        "SUPABASE_URL",  # Added missing required vars
        "SUPABASE_KEY",
    ]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        print(
            f"Missing environment variables: {', '.join(missing_vars)}. "
            "Please configure the env vars file properly."
        )
        return False
    return True
