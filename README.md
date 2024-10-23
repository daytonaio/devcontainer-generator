[![Open in Codeanywhere](https://codeanywhere.com/img/open-in-codeanywhere-btn.svg)](https://app.codeanywhere.com/#https://github.com/daytonaio/devcontainer-generator)

# DevContainer Generator

Welcome to the **devcontainer-generator** project! This tool helps you automatically generate `devcontainer.json` files for your development environments based on the structure and contents of a given GitHub repository.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Installation](#installation)
3. [Usage](#usage)
4. [Configuration](#configuration)
5. [Setting Up Daytona Workspace](#setting-up-daytona-workspace)
6. [Contributing](#contributing)
7. [License](#license)

## Project Structure

```
devcontainer-generator
├── tests.ipynb
├── requirements.txt
├── schemas
│   └── devContainer.base.schema.json
├── README.md
├── main.py
└── data
    └── devcontainers.db
```

- **tests.ipynb**: Jupyter Notebook containing tests and exploratory data analysis.
- **requirements.txt**: List of dependencies needed to run the project.
- **schemas/**: Directory containing the JSON schema for the `devcontainer.json` file.
- **README.md**: This documentation file.
- **main.py**: Main script to generate `devcontainer.json` files.
- **data/**: Directory containing the SQLite database files.

## Installation

To run this project in Daytona, you'll need to have Daytona installed. Follow these steps to set up the project:

1. **Install Daytona**:
    ```bash
    (curl -L https://download.daytona.io/daytona/install.sh | sudo bash) && daytona server stop && daytona server -y && daytona
    ```

2. **Create new project and run IDE**:
    ```bash
    daytona create https://github.com/nkkko/devcontainer-generator --code
    ```

3. **Set up environment variables**:
   Create a `.env` file in the project's root directory and add the following environment variables:
    ```dotenv
    AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
    AZURE_OPENAI_API_KEY=your_azure_openai_api_key
    AZURE_OPENAI_API_VERSION=your_azure_openai_api_version
    MODEL=your_model_name
    GITHUB_TOKEN=your_github_token
    ```

## Usage

Run the `main.py` script to start the FastHTML app and generate `devcontainer.json` files. Here's how you can do it:

```bash
python main.py
```

**Instructions:**

1. After starting the app, open your web browser and go to `http://localhost:8000`.
2. Enter the URL of the GitHub repository for which you want to generate a `devcontainer.json` file.
3. Click the "Generate devcontainer.json" button.
4. The generated `devcontainer.json` will be displayed and can be copied to your clipboard.

## Configuration

### Azure OpenAI and Instructor Clients

Ensure the following environment variables are set in your `.env` file:

```dotenv
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_API_VERSION=your_azure_openai_api_version
MODEL=your_model_name
GITHUB_TOKEN=your_github_token
```

### SQLite Database

The project uses an SQLite database to store the generated `devcontainer.json` files and their embeddings. The database is located in the `data` directory.

### JSON Schema

The JSON schema for the `devcontainer.json` file is located in `schemas/devContainer.base.schema.json`.

## Setting Up Daytona Workspace

**Steps to Set Up Daytona Workspace**

1. Create [Daytona](https://github.com/daytonaio/daytona) Workspace:

    ```bash
    daytona create https://github.com/nkkko/devcontainer-generator
    ```

2. Select Preferred IDE:

    ```bash
    daytona ide
    ```

3. Open the Workspace:

    ```bash
    daytona code
    ```

## Contributing

We welcome contributions! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to contribute to this project.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

---

Thank you for using **devcontainer-generator**! If you have any questions or issues, feel free to open an issue on GitHub.