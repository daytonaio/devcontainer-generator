import os
import requests
from dotenv import load_dotenv

def main():
    # Unset any existing GITHUB_TOKEN environment variable
    if 'GITHUB_TOKEN' in os.environ:
        del os.environ['GITHUB_TOKEN']

    # Load environment variables from .env file
    load_dotenv()

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN environment variable is not set.")
        return

    # Print all environment variables starting with GITHUB to debug
    print("Environment Variables:")
    for key, value in os.environ.items():
        if 'GITHUB' in key:
            print(f"{key}: {value[:5]}...<hidden>")

    contents_api_url = "https://api.github.com/repos/ckeditor/ckeditor5/contents"

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}",
    }

    print(f"GITHUB_TOKEN: {token[:5]}...<hidden>")
    print(f"Headers: {headers}")
    print(f"Contents API URL: {contents_api_url}")

    response = requests.get(contents_api_url, headers=headers)
    print(f"Response (standard): {response.status_code} - {response.text}")

    http_proxy = os.getenv('HTTP_PROXY', '')
    https_proxy = os.getenv('HTTPS_PROXY', '')
    print(f"HTTP_PROXY: {http_proxy}")
    print(f"HTTPS_PROXY: {https_proxy}")

    # Try turning off SSL verify just to debug if it's causing issues
    response_no_ssl = requests.get(contents_api_url, headers=headers, verify=False)
    print(f"Response (no SSL verify): {response_no_ssl.status_code} - {response_no_ssl.text}")

if __name__ == "__main__":
    main()