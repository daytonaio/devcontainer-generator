# helpers/devcontainer_helpers.py

import json
import logging
import os
import jsonschema
from helpers.jinja_helper import process_template
from schemas import DevContainerModel


def generate_devcontainer_json(instructor_client, repo_url, repo_context, max_retries=2):
    if "<<EXISTING_DEVCONTAINER>>" in repo_context:
        logging.info("Existing devcontainer.json found in the repository.")
        existing_devcontainer = (
            repo_context.split("<<EXISTING_DEVCONTAINER>>")[1]
            .split("<<END_EXISTING_DEVCONTAINER>>")[0]
            .strip()
        )
        return existing_devcontainer

    logging.info("Generating devcontainer.json...")

    template_data = {"repo_url": repo_url, "repo_context": repo_context}

    prompt = process_template("prompts/devcontainer.jinja", template_data)

    for attempt in range(max_retries + 1):
        try:
            logging.debug(f"Attempt {attempt + 1} to generate devcontainer.json")
            response = instructor_client.chat.completions.create(
                model=os.getenv("MODEL"),
                response_model=DevContainerModel,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates devcontainer.json files."},
                    {"role": "user", "content": prompt},
                ],
            )
            devcontainer_json = json.dumps(response.dict(exclude_none=True), indent=2)

            if validate_devcontainer_json(devcontainer_json):
                return devcontainer_json
            else:
                logging.warning(f"Generated JSON failed validation on attempt {attempt + 1}")
                if attempt == max_retries:
                    raise ValueError("Failed to generate valid devcontainer.json after maximum retries")
        except Exception as e:
            logging.error(f"Error on attempt {attempt + 1}: {str(e)}")
            if attempt == max_retries:
                raise

    raise ValueError("Failed to generate valid devcontainer.json after maximum retries")

def validate_devcontainer_json(devcontainer_json):
    logging.info("Validating devcontainer.json...")
    schema_path = os.path.join(os.path.dirname(__file__), "..", "schemas", "devContainer.base.schema.json")
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