from http.client import HTTPException
import logging
import os
import json
from datetime import datetime
from fasthtml.common import *
from dotenv import load_dotenv
from supabase_client import supabase

from helpers.openai_helpers import setup_azure_openai, setup_instructor
from helpers.github_helpers import fetch_repo_context, check_url_exists
from helpers.devcontainer_helpers import generate_devcontainer_json, validate_devcontainer_json
from helpers.token_helpers import count_tokens, truncate_to_token_limit
from models import DevContainer
from schemas import DevContainerModel
from content import *

# Set up logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Load environment variables
load_dotenv()

def check_env_vars():
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_API_VERSION",
        "MODEL",
        "GITHUB_TOKEN",
        "SUPABASE_URL",
        "SUPABASE_KEY",
    ]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        print(f"Missing environment variables: {', '.join(missing_vars)}. Please configure the env vars file properly.")
        return False
    return True

hdrs = [
    Script(src="https://www.googletagmanager.com/gtag/js?id=G-Q22LCTCW8Y", aync=True),
    Script("""
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
        gtag('config', 'G-Q22LCTCW8Y');
    """),
    Script("""
        (function(c,l,a,r,i,t,y){
            c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
            t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
            y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
        })(window, document, "clarity", "script", "o5om7ajkg6");
    """),
    picolink,
    Meta(charset='UTF-8'),
    Meta(name='viewport', content='width=device-width, initial-scale=1.0, maximum-scale=1.0'),
    Meta(name='description', content=description),
    *Favicon('favicon.ico', 'favicon-dark.ico'),
    *Socials(title='DevContainer.ai',
        description=description,
        site_name='devcontainer.ai',
        twitter_site='@daytonaio',
        image=f'/assets/og-sq.png',
        url=''),
    Script(src='https://cdn.jsdelivr.net/gh/gnat/surreal@main/surreal.js'),
    scopesrc,
    Link(rel="stylesheet", href="/css/main.css"),
]

# Initialize FastHTML app
app, rt = fast_app(
    hdrs=hdrs,
    live=True,
    debug=True
)

scripts = (
    Script(src="/js/main.js"),
)

from fastcore.xtras import timed_cache

# Main page composition
@timed_cache(seconds=60)
def home():
    return (Title(f"DevContainer.ai - {description}"),
        Main(
            hero_section(),
            generator_section(),
            setup_section(),
            manifesto(),
            benefits_section(),
            examples_section(),
            faq_section(),
            cta_section(),
            footer_section()),
        *scripts)


async def generateDevContainer(repo_url:str, regenerate=False):
    
    repo_url = repo_url.rstrip('/')

    try:
        exists, existing_record = check_url_exists(repo_url)
        logging.info(f"URL check result: exists={exists}, existing_record={existing_record}")

        repo_context, existing_devcontainer, devcontainer_url = fetch_repo_context(repo_url)
        logging.info(f"Fetched repo context. Existing devcontainer: {'Yes' if existing_devcontainer else 'No'}")
        logging.info(f"Devcontainer URL: {devcontainer_url}")

        if exists and not regenerate:
            logging.info(f"URL already exists in database. Returning existing devcontainer_json for: {repo_url}")
            devcontainer_json = existing_record['devcontainer_json']
            generated = existing_record['generated']
            source = "database"
            url = existing_record['devcontainer_url']
        else:
            devcontainer_json, url = generate_devcontainer_json(instructor_client, repo_url, repo_context, devcontainer_url, regenerate=regenerate)
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
                    created_at=datetime.utcnow().isoformat()  # Ensure this is a string
                )

                # Convert the Pydantic model to a dictionary and handle datetime serialization
                devcontainer_dict = json.loads(new_devcontainer.json(exclude_unset=True))

                result = supabase.table("devcontainers").insert(devcontainer_dict).execute()
                logging.info(f"Successfully saved to database with devcontainer_url: {devcontainer_url}")
            except Exception as e:
                logging.error(f"Error while saving to database: {str(e)}")
                raise
        
        return devcontainer_json, source
    except Exception as e:
        logging.error(f"Error generating devcontainer.json: {str(e)}")
        raise e


@rt("/", methods=["get"])
async def get(repo_url: str):
    if not repo_url: 
        return home()
    try: 
        devcontainer_json, source = await generateDevContainer(repo_url)
        return devcontainer_json
    except Exception as e:
        logging.error(f"Error generating devcontainer.json: {str(e)}")
        raise HTTPException(500, f"An error occurred while generating the devcontainer.json: {str(e)}")
    

@rt("/generate", methods=["post"])
async def post(repo_url: str, regenerate: bool = False):
    logging.info(f"Generating devcontainer.json for: {repo_url}")

    # Normalize the repo_url by stripping trailing slashes
    repo_url = repo_url.rstrip('/')

    try:
        devcontainer_json, source = await generateDevContainer(repo_url, regenerate=regenerate)
    
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

@rt("/manifesto")
async def get():
    return manifesto_page()

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