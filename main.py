from fasthtml.common import *
import logging
import os
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from helpers.openai_helpers import setup_azure_openai, setup_instructor
from helpers.github_helpers import fetch_repo_context, check_url_exists
from helpers.devcontainer_helpers import generate_devcontainer_json, validate_devcontainer_json
from helpers.token_helpers import count_tokens, truncate_to_token_limit
from models import DevContainer, Base
from schemas import DevContainerModel


# Set up logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Load environment variables if .env exists
load_dotenv()

# Function to check if necessary environment variables are set
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

# SQLAlchemy setup
engine = create_engine("sqlite:///data/devcontainers.db")
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

# Initialize FastHTML app
app, rt = fast_app(
    hdrs=(
        picolink,
        Link(rel="stylesheet", href="/css/main.css"),
        Script(src="/js/main.js"),
    ),
    debug=True
)

# Define routes
@rt("/")
def get():
    return Titled("AI Dev Container Generator",
        Main(
            Form(
                Group(
                    Input(type="text", name="repo_url", placeholder="Enter GitHub repository URL", cls="form-input"),
                    Button(
                        Div(
                            Img(src="assets/icons/magic-wand.svg", cls="svg-icon"),
                            Img(src="assets/icons/loading-spinner.svg", cls="htmx-indicator"),
                            cls="icon-container"
                        ),
                        Span("Generate", cls="button-text"),
                        cls="button",
                        id="generate-button",
                        hx_post="/generate",
                        hx_target="#result",
                        hx_indicator="#generate-button"
                    )
                ),
                Div(id="url-error", cls="error-message"),
                id="generate-form",
                cls="form",
                hx_post="/generate",
                hx_target="#result",
                hx_indicator=".htmx-indicator"
            ),
            Div(id="result"),
            cls="container"
        ))

@rt("/generate", methods=["post"])
async def post(session, repo_url: str, regenerate: bool = False):
    logging.info(f"Generating devcontainer.json for: {repo_url}")

    try:
        exists, existing_record = check_url_exists(repo_url, Session)
        logging.info(f"URL check result: exists={exists}, existing_record={existing_record}")

        repo_context, existing_devcontainer = fetch_repo_context(repo_url)
        logging.info(f"Fetched repo context. Existing devcontainer: {'Yes' if existing_devcontainer else 'No'}")

        if exists and not regenerate:
            logging.info(f"URL already exists in database. Returning existing devcontainer_json for: {repo_url}")
            devcontainer_json = existing_record.devcontainer_json
            generated = existing_record.generated
            source = "database"
        elif existing_devcontainer:
            logging.info("Existing devcontainer.json found in the repository.")
            devcontainer_json = existing_devcontainer
            generated = False
            source = "repository"
        else:
            devcontainer_json = generate_devcontainer_json(instructor_client, repo_url, repo_context)
            generated = True
            source = "generated"

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

                session = Session()
                new_devcontainer = DevContainer(
                    url=repo_url,
                    devcontainer_json=devcontainer_json,
                    repo_context=repo_context,
                    tokens=count_tokens(repo_context),
                    model=os.getenv("MODEL"),
                    embedding=embedding_json,
                    generated=generated,
                )
                session.add(new_devcontainer)
                session.commit()
                session.close()
                logging.info("Successfully saved to database")
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

# Serve static files
@rt("/{fname:path}.{ext:static}")
async def get(fname:str, ext:str):
    return FileResponse(f'{fname}.{ext}')

# Initialize clients
if check_env_vars():
    openai_client = setup_azure_openai()
    instructor_client = setup_instructor(openai_client)

if __name__ == "__main__":
    logging.info("Starting FastHTML app...")
    serve()