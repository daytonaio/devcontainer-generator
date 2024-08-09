# Use the same structure as examples
from fasthtml.common import *
import os
import git
import json
import subprocess
import sqlite3
from dotenv import load_dotenv
from instructor import from_openai
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv()

# Initialize the `Instructor` client
client = from_openai(OpenAI(api_key=os.getenv('AZURE_OPENAI_API_KEY')))

# FastHTML App setup
app = FastHTML(hdrs=(picolink,))
rt = app.route

# SQLite setup
conn = sqlite3.connect('data/devcontainer.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS devcontainer_specs
             (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT, devcontainer_json TEXT, vector_embedding BLOB)''')
conn.commit()

# Define the pydantic model to structure the devcontainer.json
class DevContainerSpec(BaseModel):
    json_schema: str = Field(..., alias='$schema')
    name: str
    build: dict


# Function to clone a GitHub repository
def clone_repo(repo_url, clone_dir='cloned_repo'):
    if os.path.exists(clone_dir):
        subprocess.run(['rm', '-rf', clone_dir])
    os.makedirs(clone_dir, exist_ok=True)
    git.Repo.clone_from(repo_url, clone_dir)
    return clone_dir


# Function to detect the primary language used in the repository
def detect_primary_language(clone_dir):
    lang_count = {}
    for root, _, files in os.walk(clone_dir):
        for file in files:
            if file.endswith(('.py', '.js', '.java', '.cpp', '.rb', '.go', '.php', '.cs')):
                lang = file.split('.')[-1]
                lang_count[lang] = lang_count.get(lang, 0) + 1
    return max(lang_count, key=lang_count.get) if lang_count else None


# Function to extract repo details
def extract_repo_details(repo_dir):
    # Dummy dictionary to simulate extraction
    return {
        'name': os.path.basename(repo_dir),
        'language': detect_primary_language(repo_dir),
        'dependencies': [],  # Extract actual dependencies here
        'description': 'Auto-generated devcontainer.json',
    }


# Main page for the FastHTML app
@rt("/")
def get():
    return Title("devcontainer.json Generator"), Main(
        H1("Create devcontainer.json"),
        Form(Group(Input(name="repo_url", placeholder="Enter GitHub URL", required=True),
                   Button("Create devcontainer.json")),
             hx_post="/generate", hx_target="#result", hx_swap="outerHTML"),
        Div(id="result"),
        cls='container')


# Route to generate devcontainer.json
@rt("/generate")
def post(repo_url: str):
    with st.spinner("Processing..."):
        repo_dir = clone_repo(repo_url)
        repo_details = extract_repo_details(repo_dir)

        prompt = f'Generate devcontainer.json for a project with the following details: {json.dumps(repo_details)}'
        response = client.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "Return only the json content."}, {"role": "user", "content": prompt}],
            response_model=DevContainerSpec
        )

        devcontainer_spec = response.dict()

        # Save the result in SQLite database
        c.execute('INSERT INTO devcontainer_specs (url, devcontainer_json) VALUES (?, ?)', (repo_url, json.dumps(devcontainer_spec)))
        id_ = c.lastrowid
        conn.commit()

        return Div(
            H2("Generated devcontainer.json"),
            Code(json.dumps(devcontainer_spec, indent=4)),
            Button("Copy", onclick="copyText()"),
            Script("function copyText() { navigator.clipboard.writeText(document.getElementsByTagName('code')[0].innerText); alert('Copied to clipboard!'); }"),
            cls='container')


if __name__ == "__main__":
    serve()