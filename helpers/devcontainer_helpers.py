# helpers/devcontainer_helpers.py

import json
import logging
import os
import jsonschema
import tiktoken
from helpers.jinja_helper import process_template
from schemas import DevContainerModel
from supabase_client import supabase
from models import DevContainer
import yaml


import logging
import tiktoken


def truncate_context(context, max_tokens=120000):
    logging.info(f"Starting truncate_context with max_tokens={max_tokens}")
    logging.debug(f"Initial context length: {len(context)} characters")

    encoding = tiktoken.encoding_for_model("gpt-4o-mini")
    tokens = encoding.encode(context)

    logging.info(f"Initial token count: {len(tokens)}")

    if len(tokens) <= max_tokens:
        logging.info("Context is already within token limit. No truncation needed.")
        return context

    logging.info(f"Context size is {len(tokens)} tokens. Truncation needed.")

    # Prioritize keeping the repository structure and languages
    structure_end = context.find("<<END_SECTION: Repository Structure >>")
    languages_end = context.find("<<END_SECTION: Repository Languages >>")

    logging.debug(f"Structure end position: {structure_end}")
    logging.debug(f"Languages end position: {languages_end}")

    important_content = (
        context[:languages_end] + "<<END_SECTION: Repository Languages >>\n\n"
    )
    remaining_content = context[
        languages_end + len("<<END_SECTION: Repository Languages >>\n\n") :
    ]

    important_tokens = encoding.encode(important_content)
    logging.debug(f"Important content token count: {len(important_tokens)}")

    if len(important_tokens) > max_tokens:
        logging.warning(
            "Important content alone exceeds max_tokens. Truncating important content."
        )
        important_content = encoding.decode(important_tokens[:max_tokens])
        return important_content

    remaining_tokens = max_tokens - len(important_tokens)
    logging.info(f"Tokens available for remaining content: {remaining_tokens}")

    truncated_remaining = encoding.decode(
        encoding.encode(remaining_content)[:remaining_tokens]
    )

    final_context = important_content + truncated_remaining
    final_tokens = encoding.encode(final_context)

    logging.info(f"Final token count: {len(final_tokens)}")
    logging.debug(f"Final context length: {len(final_context)} characters")

    return final_context


def generate_devcontainer_json(
    instructor_client,
    repo_url,
    repo_context,
    devcontainer_url=None,
    max_retries=2,
    regenerate=False,
):
    existing_devcontainer = None
    existing_docker_compose = None
    if "<<EXISTING_DEVCONTAINER>>" in repo_context:
        logging.info("Existing devcontainer.json found in the repository.")
        existing_devcontainer = (
            repo_context.split("<<EXISTING_DEVCONTAINER>>")[1]
            .split("<<END_EXISTING_DEVCONTAINER>>")[0]
            .strip()
        )
    if "<<EXISTING_DOCKER_COMPOSE>>" in repo_context:
        logging.info("Existing docker-compose.yml found in the repository.")
        existing_docker_compose = (
            repo_context.split("<<EXISTING_DOCKER_COMPOSE>>")[1]
            .split("<<END_EXISTING_DOCKER_COMPOSE>>")[0]
            .strip()
        )
    if not regenerate and devcontainer_url:
        logging.info(f"Using existing devcontainer.json from URL: {devcontainer_url}")
        return existing_devcontainer, existing_docker_compose, devcontainer_url

    logging.info("Generating devcontainer.json and docker-compose.yml...")

    truncated_context = truncate_context(repo_context, max_tokens=126000)

    template_data = {
        "repo_url": repo_url,
        "repo_context": truncated_context,
        "existing_devcontainer": existing_devcontainer,
        "existing_docker_compose": existing_docker_compose
    }

    prompt = process_template("prompts/devcontainer_docker_compose.jinja", template_data)

    for attempt in range(max_retries + 1):
        try:
            logging.debug(f"Attempt {attempt + 1} to generate devcontainer.json and docker-compose.yml")
            response = instructor_client.chat.completions.create(
                model=os.getenv("MODEL"),
                response_model=DevContainerModel,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates devcontainer.json and docker-compose.yml files."},
                    {"role": "user", "content": prompt},
                ],
            )
            devcontainer_json = json.dumps(response.dict(exclude={'docker_compose'}, exclude_none=True), indent=2)
            docker_compose_yml = yaml.dump(response.docker_compose.dict(exclude_none=True), sort_keys=False) if response.docker_compose else None

            if validate_devcontainer_json(devcontainer_json) and (docker_compose_yml is None or validate_docker_compose_yml(docker_compose_yml)):
                logging.info("Successfully generated and validated devcontainer.json and docker-compose.yml")
                if existing_devcontainer and existing_docker_compose and not regenerate:
                    return existing_devcontainer, existing_docker_compose, devcontainer_url
                else:
                    return devcontainer_json, docker_compose_yml, None
            else:
                logging.warning(f"Generated files failed validation on attempt {attempt + 1}")
                if attempt == max_retries:
                    raise ValueError("Failed to generate valid files after maximum retries")
        except Exception as e:
            logging.error(f"Error on attempt {attempt + 1}: {str(e)}")
            if attempt == max_retries:
                raise

    raise ValueError("Failed to generate valid files after maximum retries")


def validate_devcontainer_json(devcontainer_json):
    logging.info("Validating devcontainer.json...")
    schema_path = os.path.join(
        os.path.dirname(__file__), "..", "schemas", "devContainer.base.schema.json"
    )
    with open(schema_path, "r") as schema_file:
        schema = json.load(schema_file)
    try:
        logging.debug("Running validation...")
        jsonschema.validate(instance=json.loads(devcontainer_json), schema=schema)
        logging.info("Validation successful.")
        return True
    except jsonschema.exceptions.ValidationError as e:
        logging.error(f"Validation failed: {e}")
        return False


def validate_docker_compose_yml(docker_compose_yml):
    logging.info("Validating docker-compose.yml...")
    try:
        yaml.safe_load(docker_compose_yml)
        logging.info("Docker Compose YAML validation successful.")
        return True
    except yaml.YAMLError as e:
        logging.error(f"Docker Compose YAML validation failed: {e}")
        return False


def save_devcontainer(new_devcontainer):
    try:
        result = (
            supabase.table("devcontainers").insert(new_devcontainer.dict()).execute()
        )
        return result.data[0] if result.data else None
    except Exception as e:
        logging.error(f"Error saving devcontainer to Supabase: {str(e)}")
        raise
