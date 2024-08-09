from fasthtml.common import *
import os
import json
import requests
import instructor
from openai import AzureOpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import jsonschema
import sqlite3
import sqlite_vec

# Load environment variables
load_dotenv()

# Set up Azure OpenAI client
def setup_azure_openai():
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION")
    )

# Set up Instructor client
def setup_instructor(openai_client):
    return instructor.patch(openai_client)

# Set up SQLite database with sqlite-vec support
def setup_database():
    db = database('data/devcontainers.db')
    devcontainers = db.t.devcontainers
    if devcontainers not in db.t:
        devcontainers.create(
            url=str,
            devcontainer_json=str,
            embedding=str,
            pk='url'
        )

    # Try to load sqlite-vec SQL functions
    try:
        db.conn.enable_load_extension(True)
        db.conn.load_extension("sqlite-vec0")
    except sqlite3.OperationalError as e:
        print(f"Warning: Could not load sqlite-vec0 extension: {e}")
        print("Vector operations may not be available.")

    return db, devcontainers

# Define Pydantic model for devcontainer.json
class DevContainer(BaseModel):
    name: str = Field(description="Name of the dev container")
    image: str = Field(description="Docker image to use")
    features: dict = Field(description="Features to add to the dev container")
    forwardPorts: list[int] = Field(description="Ports to forward from the container to the local machine")
    postCreateCommand: str = Field(description="Command to run after creating the container")

# Function to fetch relevant files and context from a GitHub repository
def fetch_repo_context(repo_url):
    owner, repo = repo_url.split("/")[-2:]
    api_url = f'https://api.github.com/repos/{owner}/{repo}/contents'
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f'token {os.getenv("GITHUB_TOKEN")}'
    }
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()

    context = []
    for file in response.json():
        if file['name'] in ["requirements.txt", "Dockerfile", ".gitignore"]:
            file_content = requests.get(file['download_url']).text
            context.append(f"{file['name']}:\n{file_content}")

    return "\n\n".join(context)

# Function to generate devcontainer.json using Instructor and Azure OpenAI
def generate_devcontainer_json(instructor_client, repo_url, repo_context):
    prompt = f"""
    Given the following context from a GitHub repository:

    {repo_context}

    Generate a devcontainer.json file for this project. The file should include appropriate settings for the development environment based on the project's requirements and structure.
    """

    response = instructor_client.chat.completions.create(
        model="gpt-4",
        response_model=DevContainer,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates devcontainer.json files."},
            {"role": "user", "content": prompt}
        ]
    )

    return json.dumps(response.dict(), indent=2)

# Function to validate generated devcontainer.json against schema
def validate_devcontainer_json(devcontainer_json):
    schema_path = os.path.join(os.path.dirname(__file__), "schemas", "devContainer.base.schema.json")
    with open(schema_path, 'r') as schema_file:
        schema = json.load(schema_file)
    try:
        jsonschema.validate(instance=json.loads(devcontainer_json), schema=schema)
        return True
    except jsonschema.exceptions.ValidationError:
        return False

# Set up FastHTML app
app = FastHTML()
rt = app.route

# Landing page route
@rt("/")
def home():
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
async def generate(repo_url: str):
    try:
        # Fetch repository context
        repo_context = fetch_repo_context(repo_url)

        # Generate devcontainer.json
        devcontainer_json = generate_devcontainer_json(instructor_client, repo_url, repo_context)

        # Validate devcontainer.json
        is_valid = validate_devcontainer_json(devcontainer_json)

        if is_valid:
            # Save to database
            if hasattr(openai_client.embeddings, 'create'):
                embedding = openai_client.embeddings.create(input=devcontainer_json, model="text-embedding-ada-002").data[0].embedding
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
        return Div(
            H2("Error"),
            P(f"An error occurred: {str(e)}")
        )

# Set up and run the app
if __name__ == "__main__":
    # Initialize clients and database
    openai_client = setup_azure_openai()
    instructor_client = setup_instructor(openai_client)
    db, devcontainers = setup_database()

    serve()