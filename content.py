from fasthtml.common import *

description = 'Generate Custom Dev Containers in Seconds with AI'
_blank = dict(target="_blank", rel="noopener noreferrer")

def hero_section():
    return Section(
        Div(
            H1("AI-Powered Dev Container Generator", cls="text-3xl font-bold text-center"),
            H2("Simplify your development workflow with AI-powered dev container configurations"),
            P("Generate customized devcontainer.json files from GitHub repositories with ease.", cls="text-lg text-center mt-4"),
            cls="container mx-auto px-4 py-16"
        ),
        cls="bg-gray-100",
    )


def generator_section():
    return Section(
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
    )

def benefits_section():
    return Section(
        Div(
            H2("Benefits of Using Dev Containers", cls="text-2xl font-bold text-center mb-8"),
            Div(
                benefit_card("Consistency", "Ensure every team member uses the same development environment, regardless of their local setup."),
                benefit_card("Reproducibility", "Easily recreate a specific development environment for bug reproduction or testing."),
                benefit_card("Isolation", "Keep project dependencies contained, preventing conflicts with other projects."),
                benefit_card("Onboarding", "Simplify onboarding for new developers by providing a ready-to-go environment."),
                cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 container mx-auto",
            ),
            cls="container mx-auto px-4 py-16",
        ),
        cls="bg-gray-100"
    )

def benefit_card(title, description):
    return Div(
        H3(title, cls="text-xl font-bold mb-2"),
        P(description, cls="text-gray-700"),
        cls="bg-white rounded-md shadow-md p-6"
    )

def setup_section():
    return Section(
        Div(
            H2("Setting Up Dev Containers in Your Repository", cls="text-2xl font-bold text-center mb-8"),
            P("Once you have your `devcontainer.json` file, follow these steps:", cls="text-gray-700 container mx-auto mb-4"),
            Ul(
                Li("Create a `.devcontainer` directory in the root of your repository."),
                Li("Place the `devcontainer.json` file inside the `.devcontainer` directory."),
                Li("(Optional) Add a `Dockerfile` to the `.devcontainer` directory if you need to customize the base image further."),
                Li("Open your repository in VS Code or ",
                    A("Daytona", href="https://daytona.io", **_blank,
                        cls="border-b-2 border-b-black/30 hover:border-b-black/80"),
                   "and it will automatically detect the dev container configuration."),
                cls="list-decimal list-inside text-gray-700 mb-8"
            ),
            P("Now you're ready to develop inside your consistent and isolated environment!", cls="text-gray-700 container mx-auto"),
            cls="container mx-auto px-4 py-16"
        ),
    )

def examples_section():
    return Section(
        Div(
            H2("Examples from Popular Repositories", cls="text-2xl font-bold text-center mb-8"),
            P("Explore how popular projects utilize dev containers for efficient development:", cls="text-gray-700 text-center mb-8 container mx-auto"),
            Div(
                example_card("Microsoft/vscode", "https://github.com/microsoft/vscode/tree/main/.devcontainer"),
                example_card("daytonaio/daytona", "https://github.com/daytonaio/daytona/blob/main/.devcontainer"),
                example_card("withastro/astro", "https://github.com/withastro/astro/tree/main/.devcontainer"),
                cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 container mx-auto",
            ),
            cls="container mx-auto px-4 py-16"
        ),
        cls="bg-gray-100"
    )

def example_card(repo_name, url):
    return Div(
        A(repo_name, href=url, target="_blank", cls="text-lg font-bold hover:underline"),
        cls="bg-white rounded-md shadow-md p-6"
    )

def faq_section():
    return Section(
        Div(
            H2("Frequently Asked Questions", cls="text-2xl font-bold text-center mb-8"),
            Div(
                faq_item("What are the advantages of using a dev container?",
                         "Dev containers provide a consistent and isolated environment for development, ensuring that all team members have the same setup and dependencies."),
                faq_item("How does the dev container generation process work?",
                         "The process is simple: 1) Enter your GitHub repo URL, 2) Our AI analyzes your project, 3) Get a custom devcontainer.json in seconds, 4) Start coding in your optimized environment."),
                faq_item("Which development tools are compatible with the generated dev containers?",
                         "Our generated dev containers work seamlessly with Daytona, VS Code, GitHub Codespaces, and other popular dev tools."),
                faq_item("What are the advantages of using a dev container?",
                         "Dev containers provide a consistent and isolated environment for development, ensuring that all team members have the same setup and dependencies."),
                faq_item("Can I customize the generated dev container?",
                         "Yes, you can further customize the dev container for example by adding a `Dockerfile` to the `.devcontainer` directory or adding more Dev Container features."),
                faq_item("What if my repository already has a dev container?",
                         "Our generator will detect existing `devcontainer.json` files and try to use them as a starting point for customization. You can also choose to regenerate a new configuration."),
                faq_item("How often should I update my dev container configuration?",
                         "It's a good practice to update your dev container configuration whenever you make significant changes to your project's dependencies or development environment. You can easily regenerate the configuration using our tool."),
                faq_item("Does this service work with private GitHub repositories?",
                         "Currently, our dev container generator only works with public GitHub repositories. This ensures that we can analyze the necessary metadata without requiring additional authentication or permissions."),
                cls="accordion container mx-auto",
            ),
            cls="container mx-auto px-4 py-16",
        ),
    )

def faq_item(question, answer):
    return Div(
        H3(question, cls="text-lg font-medium cursor-pointer"),
        Div(P(answer, cls="text-gray-700 mt-2"), cls="hidden"),
        cls="mb-4",
        **{"_surreal": "on click toggle class:hidden for next-sibling"}
    )

def cta_section():
    return Section(
        Div(
            H2("Ready to Simplify Your Development Environment?", cls="text-2xl font-bold text-center mb-4"),
            P("Experience the power of Daytona's flexible and secure development environment platform.", cls="text-lg text-center mb-6"),
            A(
                Div(
                    Img(src="assets/icons/github-mark-white.svg", cls="svg-icon"),
                    cls="icon-container"
                ),
                Span("Get Daytona Now", cls="button-text"),
                role="button",
                href="https://github.com/daytonaio/daytona",
                title="Get Daytona",
            ),
            cls="container mx-auto px-4 py-16 text-center"
        ),
        cls="bg-gray-100"
    )

def footer_section():
    return Footer(
        Div(
            P("© 2024 ",
              A("Daytona Platforms Inc.", href="https://daytona.io", **_blank,
                cls="border-b-2 border-b-black/30 hover:border-b-black/80"),
              "All rights reserved.", cls="text-center text-gray-600"),
            cls="container mx-auto px-4 py-8"
        ),
        cls="bg-gray-100",
    )