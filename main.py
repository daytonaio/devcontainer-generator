from fasthtml.common import *
import os
import json
import requests
import instructor
from openai import AzureOpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError
import jsonschema
import sqlite3
import sqlite_vec
import tiktoken
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Function to check if necessary environment variables are set
def check_env_vars():
    required_vars = ['AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_API_KEY', 'AZURE_OPENAI_API_VERSION', 'MODEL', 'GITHUB_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Missing environment variables: {', '.join(missing_vars)}. Please configure the .env file properly.")
        return False
    return True

def count_tokens(text):
    # Instantiate the tiktoken encoder for the model you are using, e.g., "gpt-3.5-turbo"
    encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokens = encoder.encode(text)
    return len(tokens)

# Set up Azure OpenAI client
def setup_azure_openai():
    logging.info("Setting up Azure OpenAI client...")
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION")
    )

# Set up Instructor client
def setup_instructor(openai_client):
    logging.info("Setting up Instructor client...")
    return instructor.patch(openai_client)

# Set up SQLite database with sqlite-vec support
def setup_database():
    logging.info("Setting up SQLite database...")
    db = database('data/devcontainers.db')
    devcontainers = db.t.devcontainers
    if devcontainers not in db.t:
        logging.info("Creating devcontainers table...")
        devcontainers.create(
            url=str,
            devcontainer_json=str,
            embedding=str,
            pk='url'
        )

    # Try to load sqlite-vec SQL functions
    try:
        logging.info("Trying to load sqlite-vec0 extension...")
        db.conn.enable_load_extension(True)
        db.conn.load_extension("sqlite-vec0")
        logging.info("sqlite-vec0 extension loaded successfully.")
    except sqlite3.OperationalError as e:
        logging.warning(f"Could not load sqlite-vec0 extension: {e}")
        logging.warning("Vector operations may not be available.")

    return db, devcontainers

# Define Pydantic model for devcontainer.json
class DevContainer(BaseModel):
    name: str = Field(description="Name of the dev container")
    image: str = Field(description="Docker image to use")
    #features: dict = Field(description="Features to add to the dev container")
    forwardPorts: list[int] = Field(description="Ports to forward from the container to the local machine")
    postCreateCommand: str = Field(description="Command to run after creating the container")

# Function to fetch relevant files and context from a GitHub repository
def fetch_repo_context(repo_url):
    logging.info(f"Fetching context from GitHub repository: {repo_url}")
    token = os.getenv("GITHUB_TOKEN")

    # Extract owner and repository from the URL
    parts = repo_url.split("/")
    owner = parts[-2]  # Take the second-to-last part for the owner
    repo = parts[-1]  # Take the last part for the repository name

    # Base URLs for GitHub API requests
    contents_api_url = f'https://api.github.com/repos/{owner}/{repo}/contents'
    languages_api_url = f'https://api.github.com/repos/{owner}/{repo}/languages'

    # Headers for the API requests
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f'token {token}'
    }

    # Initialize context list
    context = []
    total_tokens = 0

    def traverse_dir(api_url, prefix=""):
        logging.info(f"Traversing directory: {api_url}")
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()

        structure = []
        important_files = [
            "requirements.txt", "Dockerfile", ".gitignore", "package.json", "Gemfile", "README.md",
            ".env.example", "Pipfile", "setup.py", "Pipfile.lock", "pyproject.toml",
            "CMakeLists.txt", "Makefile", "go.mod", "go.sum", "pom.xml", "build.gradle",
            "Cargo.toml", "Cargo.lock", "composer.json", "phpunit.xml", "mix.exs",
            "pubspec.yaml", "stack.yaml", "DESCRIPTION", "NAMESPACE", "Rakefile"
        ]

        for item in response.json():
            logging.debug(f"Processing item: {item['name']}")
            if item['type'] == 'dir':
                structure.append(f"{prefix}{item['name']}/")
                structure.extend(traverse_dir(item['url'], prefix=prefix + "    "))
            else:
                structure.append(f"{prefix}{item['name']}")

            # Fetch contents of specific files
            if item['name'] in important_files:
                logging.debug(f"Fetching content of {item['name']}")
                file_content = requests.get(item['download_url']).text
                content_text = f"<<SECTION: Content of {item['name']} >>\n{file_content}" + f"\n<<END_SECTION: Content of {item['name']} >>"
                context.append(content_text)

                # Count tokens in the content
                file_tokens = count_tokens(content_text)
                nonlocal total_tokens
                total_tokens += file_tokens

        return structure

    # Build the repository structure by traversing the root directory
    logging.info("Building repository structure...")
    repo_structure = traverse_dir(contents_api_url)

    # Add repository structure to context
    logging.info("Adding repository structure to context...")
    repo_structure_text = "<<SECTION: Repository Structure >>\n" + "\n".join(repo_structure) + "\n<<END_SECTION: Repository Structure >>"
    context.insert(0, repo_structure_text)

    # Count tokens in the repo structure
    repo_structure_tokens = count_tokens(repo_structure_text)
    total_tokens += repo_structure_tokens

    # Make request to fetch repository languages
    logging.info("Fetching repository languages...")
    languages_response = requests.get(languages_api_url, headers=headers)
    languages_response.raise_for_status()

    # Add repository languages to context
    logging.info("Adding repository languages to context...")
    languages_data = languages_response.json()
    languages_context = "<<SECTION: Repository Languages >>\n" + "\n".join([f"{lang}: {count} lines" for lang, count in languages_data.items()]) + "\n<<END_SECTION: Repository Languages >>"
    context.append(languages_context)

    # Count tokens in the languages context
    languages_tokens = count_tokens(languages_context)
    total_tokens += languages_tokens

    logging.debug(f"Total tokens: {total_tokens}")

    # Return the combined context
    return "\n\n".join(context)

# Function to generate devcontainer.json using Instructor and Azure OpenAI
def generate_devcontainer_json(instructor_client, repo_url, repo_context):
    logging.info("Generating devcontainer.json...")
    prompt = f"""
    Given the following context from a GitHub repository:

    {repo_context}

    Generate a devcontainer.json file for this project. The file should include appropriate settings for the development environment based on the project's requirements and structure. The 'features' field is essential and should include a dictionary of features to enable within the container.

    Here's an example of a devcontainer.json with the 'features' field:
    ```json
    {{
    "name": "Example Dev Container",
    "image": "node:16",
    "features": {{
        "ghcr.io/devcontainers/features/node": {{
        "version": "latest"
        }}
    }},
    "forwardPorts": [3000],
    "postCreateCommand": "npm install"
    }}
    ```
    """

    logging.debug(f"Prompt sent to Instructor: {prompt}")
    response = instructor_client.chat.completions.create(
        model=os.getenv("MODEL"),
        response_model=DevContainer,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates devcontainer.json files."},
            {"role": "user", "content": prompt}
        ]
    )
    logging.debug(f"Raw OpenAI Response: {response.model_dump()}")
    logging.debug(f"Instructor response: {response}")
    return json.dumps(response.dict(), indent=2)


# Function to validate generated devcontainer.json against schema
def validate_devcontainer_json(devcontainer_json):
    logging.info("Validating devcontainer.json...")
    schema_path = os.path.join(os.path.dirname(__file__), "schemas", "devContainer.base.schema.json")
    with open(schema_path, 'r') as schema_file:
        schema = json.load(schema_file)
    try:
        logging.debug("Running validation...")
        jsonschema.validate(instance=json.loads(devcontainer_json), schema=schema)
        logging.info("Validation successful.")
        return True
    except jsonschema.exceptions.ValidationError as e:
        logging.error(f"Validation failed: {e}")
        return False

# Set up FastHTML app
app = FastHTML()
rt = app.route

# Landing page route
@rt("/")
def get():
    logging.info("Rendering landing page...")
    return Title("DevContainer Generator"), Main(
        H1("DevContainer.json Generator"),
        Form(
            Input(type="text", name="repo_url", placeholder="Enter GitHub repository URL"),
            Button("Generate devcontainer.json"),
            hx_post="/generate",
            hx_target="#result"
        ),
        Div(id="result"),
        cls="container"
    )

# Generation route
@rt("/generate")
async def post(repo_url: str):
    logging.info(f"Generating devcontainer.json for: {repo_url}")
    try:
        # Fetch repository context
        repo_context = fetch_repo_context(repo_url)

        # Generate devcontainer.json
        devcontainer_json = generate_devcontainer_json(instructor_client, repo_url, repo_context)

        # Validate devcontainer.json
        is_valid = validate_devcontainer_json(devcontainer_json)

        if is_valid:
            # Save to database
            logging.info("Saving to database...")
            if hasattr(openai_client.embeddings, 'create'):
                embedding = openai_client.embeddings.create(input=devcontainer_json, model=os.getenv("EMBEDDING")).data[0].embedding
                embedding_json = json.dumps(embedding)
            else:
                embedding_json = None

            devcontainers.insert(url=repo_url, devcontainer_json=devcontainer_json, embedding=embedding_json)

            return Div(
                H2("Generated devcontainer.json"),
                Pre(Code(devcontainer_json)),
                Button("Copy to Clipboard", onclick="copyToClipboard()"),
                Script("""
                    function copyToClipboard() {
                        const code = document.querySelector('pre code').textContent;
                        navigator.clipboard.writeText(code);
                        alert('Copied to clipboard!');
                    }
                """)
            )
        else:
            return Div(
                H2("Error"),
                P("Generated devcontainer.json is not valid according to the schema.")
            )
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return Div(
            H2("Error"),
            P(f"An error occurred: {str(e)}")
        )

# Initialize clients and database
if check_env_vars():
    openai_client = setup_azure_openai()
    instructor_client = setup_instructor(openai_client)
    db, devcontainers = setup_database()

# Set up and run the app
if __name__ == "__main__":
    logging.info("Starting FastHTML app...")
    serve()