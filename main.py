import logging
import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from supabase_client import supabase
from fasthtml.common import *
from helpers.openai_helpers import setup_azure_openai, setup_instructor
from helpers.github_helpers import fetch_repo_context, check_url_exists
from helpers.devcontainer_helpers import generate_devcontainer_json_with_ports, find_ports_in_files  # Updated imports
from helpers.token_helpers import count_tokens, truncate_to_token_limit
from models import DevContainer
from schemas import DevContainerModel
from content import *

# Set up logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Load environment variables
load_dotenv()

# Modify the existing post function
@rt("/generate", methods=["post"])
async def post(repo_url: str, regenerate: bool = False):
    logging.info(f"Generating devcontainer.json for: {repo_url}")

    # Normalize the repo_url by stripping trailing slashes
    repo_url = repo_url.rstrip('/')

    try:
        exists, existing_record = check_url_exists(repo_url)
        logging.info(f"URL check result: exists={exists}, existing_record={existing_record}")

        repo_context, existing_devcontainer, devcontainer_url = fetch_repo_context(repo_url)
        logging.info(f"Fetched repo context. Existing devcontainer: {'Yes' if existing_devcontainer else 'No'}")
        logging.info(f"Devcontainer URL: {devcontainer_url}")

        # Detect relevant ports in the repository using the new helper function
        ports = find_ports_in_files(repo_url)  # Updated function call
        logging.info(f"Detected ports for forwarding: {ports}")

        if exists and not regenerate:
            logging.info(f"URL already exists in database. Returning existing devcontainer_json for: {repo_url}")
            devcontainer_json = existing_record['devcontainer_json']
            generated = existing_record['generated']
            source = "database"
            url = existing_record['devcontainer_url']
        else:
            # Generate devcontainer.json with the detected ports
            devcontainer_json, url = generate_devcontainer_json_with_ports(repo_url, ports)  # Updated function call
            generated = True
            source = "generated" if url is None else "repository"

        if not exists or regenerate:
            logging.info("Saving to database...")
            try:
                if hasattr(openai_client.embeddings, "create"):
                    embedding_model = os.getenv("EMBEDDING", "text-embedding-ada-002")
                    max_tokens = int(os.getenv("EMBEDDING_MODEL_MAX_TOKENS", 8192))

                    truncated_context = truncate_to_token_limit(repo_context, embedding_model, max_tokens)

                    embedding = openai_client.embeddings.create(input=truncated_context, model=embedding_model).data[0].embedding
                    embedding_json = json.dumps(embedding)
                else:
                    embedding_json = None

                new_devcontainer = DevContainer(
                    url=repo_url,
                    devcontainer_json=devcontainer_json,
                    devcontainer_url=devcontainer_url,
                    repo_context=repo_context,
                    tokens=count_tokens(repo_context),
                    model=os.getenv("MODEL"),
                    embedding=embedding_json,
                    generated=generated,
                    created_at=datetime.utcnow().isoformat()
                )

                # Convert the Pydantic model to a dictionary and handle datetime serialization
                devcontainer_dict = json.loads(new_devcontainer.json(exclude_unset=True))

                result = supabase.table("devcontainers").insert(devcontainer_dict).execute()
                logging.info(f"Successfully saved to database with devcontainer_url: {devcontainer_url}")
            except Exception as e:
                logging.error(f"Error while saving to database: {str(e)}")
                raise

        return Div(
            Article(f"Devcontainer.json {'found in ' + source if source in ['database', 'repository'] else 'generated'}"),
            Pre(
                Code(devcontainer_json, id="devcontainer-code", cls="overflow-auto"),
                Div(
                    Button(
                        Img(cls="w-4 h-4", src="assets/icons/copy-icon.svg", alt="Copy"),
                        cls="icon-button copy-button",
                        title="Copy to clipboard",
                    ),
                    Button(
                        Img(cls="w-4 h-4", src="assets/icons/regenerate.svg", alt="Regenerate"),
                        cls="icon-button regenerate-button",
                        hx_post=f"/generate?regenerate=true&repo_url={repo_url}",
                        hx_target="#result",
                        hx_indicator="#action-text",
                        title="Regenerate",
                    ),
                    Span(cls="action-text", id="action-text"),
                    cls="button-group"
                ),
                cls="code-container relative"
            )
        )
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        return Div(H2("Error"), P(f"An error occurred: {str(e)}"))
