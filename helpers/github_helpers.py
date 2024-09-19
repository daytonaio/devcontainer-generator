import os
import re
import logging
import requests
from helpers.token_helpers import count_tokens
from models import DevContainer
from supabase_client import supabase

def is_valid_github_url(url):
    pattern = r"^https?://github\.com/[\w-]+/[\w.-]+/?$"
    return re.match(pattern, url) is not None

def fetch_repo_context(repo_url, max_depth=1):
    # First, check if the URL is valid
    if not is_valid_github_url(repo_url):
        logging.error(f"Invalid GitHub repository URL: {repo_url}")
        raise ValueError("Invalid GitHub repository URL")

    logging.info(f"Fetching context from GitHub repository: {repo_url}")
    token = os.getenv("GITHUB_TOKEN")

    parts = repo_url.split("/")
    owner = parts[-2]
    repo = parts[-1]

    contents_api_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
    languages_api_url = f"https://api.github.com/repos/{owner}/{repo}/languages"

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}",
    }

    existing_devcontainer = None
    devcontainer_url = None

    root_devcontainer_url = f"{contents_api_url}/.devcontainer.json"
    response = requests.get(root_devcontainer_url, headers=headers)
    if response.status_code == 200:
        existing_devcontainer = requests.get(response.json()["download_url"]).text
        devcontainer_url = response.json()["download_url"]

    if not existing_devcontainer:
        devcontainer_dir_url = f"{contents_api_url}/.devcontainer"
        response = requests.get(devcontainer_dir_url, headers=headers)
        if response.status_code == 200:
            for item in response.json():
                if item["name"] == "devcontainer.json":
                    existing_devcontainer = requests.get(item["download_url"]).text
                    devcontainer_url = item["download_url"]
                    break

    context = []
    total_tokens = 0

    def traverse_dir(api_url, depth=0, prefix=""):
        if depth > max_depth:
            return []

        logging.info(f"Traversing directory: {api_url}")
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()

        structure = []
        important_files = [
            "requirements.txt", "Dockerfile", ".gitignore", "package.json",
            "Gemfile", "README.md", ".env.example", "Pipfile", "setup.py",
            "Pipfile.lock", "pyproject.toml", "CMakeLists.txt", "Makefile",
            "go.mod", "go.sum", "pom.xml", "build.gradle", "Cargo.toml",
            "Cargo.lock", "composer.json", "phpunit.xml", "mix.exs",
            "pubspec.yaml", "stack.yaml", "DESCRIPTION", "NAMESPACE", "Rakefile",
        ]
        large_dirs_to_skip = ["node_modules", "vendor"]

        for item in response.json():
            logging.debug(f"Processing item: {item['name']}")
            if item["type"] == "dir":
                if item["name"] in large_dirs_to_skip:
                    continue
                structure.append(f"{prefix}{item['name']}/")
                structure.extend(
                    traverse_dir(item["url"], depth + 1, prefix=prefix + "    ")
                )
            else:
                structure.append(f"{prefix}{item['name']}")

            if item["type"] == "file" and item["name"] in important_files:
                logging.debug(f"Fetching content of {item['name']}")
                file_content = requests.get(item["download_url"]).text
                content_text = (
                    f"<<SECTION: Content of {item['name']} >>\n{file_content}"
                    + f"\n<<END_SECTION: Content of {item['name']} >>"
                )
                context.append(content_text)

                file_tokens = count_tokens(content_text)
                nonlocal total_tokens
                total_tokens += file_tokens

        return structure

    logging.info("Building repository structure...")
    repo_structure = traverse_dir(contents_api_url)

    logging.info("Adding repository structure to context...")
    repo_structure_text = (
        "<<SECTION: Repository Structure >>\n"
        + "\n".join(repo_structure)
        + "\n<<END_SECTION: Repository Structure >>"
    )
    context.insert(0, repo_structure_text)

    repo_structure_tokens = count_tokens(repo_structure_text)
    total_tokens += repo_structure_tokens

    logging.info("Fetching repository languages...")
    languages_response = requests.get(languages_api_url, headers=headers)
    languages_response.raise_for_status()

    logging.info("Adding repository languages to context...")
    languages_data = languages_response.json()
    languages_context = (
        "<<SECTION: Repository Languages >>\n"
        + "\n".join(
            [f"{lang}: {count} lines" for lang, count in languages_data.items()]
        )
        + "\n<<END_SECTION: Repository Languages >>"
    )
    context.append(languages_context)

    languages_tokens = count_tokens(languages_context)
    total_tokens += languages_tokens

    logging.debug(f"Total tokens: {total_tokens}")

    if existing_devcontainer:
        devcontainer_context = (
            "<<SECTION: Existing devcontainer.json >>\n"
            f"{existing_devcontainer}\n"
            "<<END_SECTION: Existing devcontainer.json >>"
        )
        context.append(devcontainer_context)
        total_tokens += count_tokens(devcontainer_context)

    return "\n\n".join(context), existing_devcontainer, devcontainer_url

def check_url_exists(url):
    existing = supabase.table("devcontainers").select("*").eq("url", url).order("created_at", desc=True).limit(1).execute()
    existing_record = existing.data[0] if existing.data else None
    return existing_record is not None, existing_record