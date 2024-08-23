from fasthtml.common import *
import os
import json
import requests
import instructor
from openai import AzureOpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError
import jsonschema
import logging
from helpers.jinja_helper import process_template
from sqlalchemy import create_engine, Column, String, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import tiktoken

print("Environment variables:")
for key, value in os.environ.items():
    print(f"{key}: {value}")

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
# load_dotenv()


# SQLAlchemy setup
Base = declarative_base()
engine = create_engine('sqlite:///data/devcontainers.db')
Session = sessionmaker(bind=engine)

class DevContainer(Base):
    __tablename__ = 'devcontainers'

    url = Column(String, primary_key=True)
    devcontainer_json = Column(Text)
    repo_context = Column(Text)
    tokens = Column(Integer)
    model = Column(Text)
    embedding = Column(Text)

Base.metadata.create_all(engine)


# Function to check if necessary environment variables are set
def check_env_vars():
    required_vars = ['AZURE_OPENAI_ENDPOINT',
                     'AZURE_OPENAI_API_KEY',
                     'AZURE_OPENAI_API_VERSION',
                     'MODEL', 'GITHUB_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Missing environment variables: {', '.join(missing_vars)}. "
              "Please configure the .env file properly.")
        return False
    return True


def count_tokens(text):
    # Instantiate the tiktoken encoder for the model you are using, e.g., "gpt-3.5-turbo"
    encoder = tiktoken.encoding_for_model("gpt-4o")
    tokens = encoder.encode(text)
    return len(tokens)


# Truncate text to a specific number of tokens
def truncate_to_token_limit(text, model_name, max_tokens):
    encoding = tiktoken.encoding_for_model(model_name)
    tokens = encoding.encode(text)
    if len(tokens) > max_tokens:
        truncated_tokens = tokens[:max_tokens]
        return encoding.decode(truncated_tokens)
    return text


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


# Function to check if the URL already exists in the database
def check_url_exists(url):
    session = Session()
    existing = session.query(DevContainer).filter_by(url=url).first()
    session.close()
    return existing is not None, existing


# Define Pydantic model for devcontainer.json
class DevContainerModel(BaseModel):
    name: str = Field(description="Name of the dev container")
    image: str = Field(description="Docker image to use")
    forwardPorts: Optional[list[int]] = Field(description="Ports to forward from the container to the local machine")
    customizations: Optional[dict] = Field(None, description="Tool-specific configuration")
    settings: Optional[dict] = Field(None, description="VS Code settings to configure the development environment")
    postCreateCommand: Optional[str] = Field(description="Command to run after creating the container")


# Initialize total tokens variable (global scope)
total_tokens = 0


# Function to fetch relevant files and context from a GitHub repository
def fetch_repo_context(repo_url, max_depth=1):
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
    global total_tokens  # Referencing the global total token counter
    total_tokens = 0  # Reset to 0 before counting

    def traverse_dir(api_url, depth=0, prefix=""):
        if depth > max_depth:
            return []

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
        large_dirs_to_skip = ["node_modules", "vendor"]

        for item in response.json():
            logging.debug(f"Processing item: {item['name']}")
            if item['type'] == 'dir':
                if item['name'] in large_dirs_to_skip:
                    continue
                structure.append(f"{prefix}{item['name']}/")
                structure.extend(traverse_dir(item['url'], depth + 1, prefix=prefix + "    "))
            else:
                structure.append(f"{prefix}{item['name']}")

            # Fetch contents of specific files
            if item['type'] == 'file' and item['name'] in important_files:
                logging.debug(f"Fetching content of {item['name']}")
                file_content = requests.get(item['download_url']).text
                content_text = f"<<SECTION: Content of {item['name']} >>\n{file_content}" + f"\n<<END_SECTION: Content of {item['name']} >>"
                context.append(content_text)

                # Count tokens in the content
                file_tokens = count_tokens(content_text)
                global total_tokens  # Use global keyword to modify the global total_tokens variable
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
def generate_devcontainer_json(instructor_client, repo_url, repo_context, max_retries=2):
    logging.info("Generating devcontainer.json...")

    template_data = {
        "repo_url": repo_url,
        "repo_context": repo_context
    }

    prompt = process_template("prompts/devcontainer.jinja", template_data)

    for attempt in range(max_retries + 1):
        try:
            logging.debug(f"Attempt {attempt + 1} to generate devcontainer.json")
            response = instructor_client.chat.completions.create(
                model=os.getenv("MODEL"),
                response_model=DevContainerModel,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates devcontainer.json files."},
                    {"role": "user", "content": prompt}
                ]
            )
            devcontainer_json = json.dumps(response.dict(exclude_none=True), indent=2)

            # Validate the generated JSON
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
app = FastHTML(
    hdrs=(
        picolink,
        Style("""
            :root { --pico-font-size: 100%; }
            body { padding: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            pre { background-color: #f4f4f4; padding: 15px; border-radius: 5px; }
            .button-group { display: flex; gap: 10px; margin-top: 10px; }
        """)
    )
)
rt = app.route

# Landing page route
@rt("/")
def get():
    logging.info("Rendering landing page...")
    return Title("DevContainer Generator"), Main(
        H1("DevContainer.json Generator", cls="text-center"),
        Form(
            Input(type="text", name="repo_url", placeholder="Enter GitHub repository URL", cls="form-input"),
            Button("Generate devcontainer.json", cls="button"),
            hx_post="/generate",
            hx_target="#result",
            cls="form"
        ),
        Div(id="result"),
        cls="container"
    )

# Generation route
@rt("/generate", methods=['post', 'get'])
async def post(repo_url: str, regenerate: bool = False):
    logging.info(f"Generating devcontainer.json for: {repo_url}")
    try:
        # Check if URL already exists in the database
        exists, existing_record = check_url_exists(repo_url)

        if exists and not regenerate:
            logging.info(f"URL already exists. Returning existing devcontainer_json for: {repo_url}")
            devcontainer_json = existing_record.devcontainer_json
            return Div(
                P("A generated devcontainer.json already exists for this repository."),
                Pre(Code(devcontainer_json)),
                Div(
                    Button("Copy to Clipboard", onclick="copyToClipboard()", cls="button"),
                    Button("Regenerate", hx_post=f"/generate?repo_url={repo_url}&regenerate=true", hx_target="#result", cls="button"),
                    cls="button-group"
                ),
                Script("""
                    function copyToClipboard() {
                        const code = document.querySelector('pre code').textContent;
                        navigator.clipboard.writeText(code);
                        alert('Copied to clipboard!');
                    }
                """)
            )
        else:
            # Fetch repository context
            repo_context = fetch_repo_context(repo_url)

            # Generate devcontainer.json with retries
            try:
                devcontainer_json = generate_devcontainer_json(instructor_client, repo_url, repo_context)
            except ValueError as e:
                return Div(
                    H2("Error"),
                    P(f"Failed to generate valid devcontainer.json: {str(e)}")
                )

            # Save to database
            logging.info("Saving to database...")
            if hasattr(openai_client.embeddings, 'create'):
                embedding_model = os.getenv("EMBEDDING", "text-embedding-ada-002")
                max_tokens = int(os.getenv("EMBEDDING_MODEL_MAX_TOKENS", 8192))

                # Truncate the repo_context for embedding
                truncated_context = truncate_to_token_limit(repo_context, embedding_model, max_tokens)

                embedding = openai_client.embeddings.create(input=truncated_context, model=embedding_model).data[0].embedding
                embedding_json = json.dumps(embedding)
            else:
                embedding_json = None

            session = Session()
            if exists:
                existing_record.devcontainer_json = devcontainer_json
                existing_record.repo_context = repo_context
                existing_record.tokens = total_tokens
                existing_record.embedding = embedding_json
            else:
                new_devcontainer = DevContainer(url=repo_url, devcontainer_json=devcontainer_json, repo_context=repo_context, tokens=total_tokens, model=os.getenv("MODEL"), embedding=embedding_json)
                session.add(new_devcontainer)
            session.commit()
            session.close()

        return Div(
            P("Generated devcontainer.json"),
            Pre(Code(devcontainer_json)),
            Div(
                Button("Copy to Clipboard", onclick="copyToClipboard()", cls="button"),
                Button("Generate New", hx_get="/", hx_target="body", cls="button"),
                cls="button-group"
            ),
            Script("""
                function copyToClipboard() {
                    const code = document.querySelector('pre code').textContent;
                    navigator.clipboard.writeText(code);
                    alert('Copied to clipboard!');
                }
            """)
        )
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return Div(
            H2("Error"),
            P(f"An error occurred: {str(e)}")
        )


# Initialize clients
if check_env_vars():
    openai_client = setup_azure_openai()
    instructor_client = setup_instructor(openai_client)

# Set up and run the app
if __name__ == "__main__":
    logging.info("Starting FastHTML app...")
    serve()