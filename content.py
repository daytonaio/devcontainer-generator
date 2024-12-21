from fasthtml.common import *

description = 'Generate Custom Dev Containers in Seconds with AI'
_blank = dict(target="_blank", rel="noopener noreferrer")

def caution_section():
    return Div(
        H3(
            "⚠️ Caution: AI Generated Code",
            cls="text-2xl font-bold text-center mb-4",
            style="padding-left: 20px; padding-top: 10px; padding-bottom: 10px;"
        ),
        Ul(
            Li("Make sure to review the generated devcontainer.json file before running it in your development environment."),
            Li("The best way to run AI generated code is inside sandboxed dev environments like those managed by Daytona."),
            cls="list-disc list-inside text-lg text-center mt-4"
        ),
        cls="container mx-auto px-4 py-16 bg-yellow-100",
        style="background-color: #ffff66; padding-bottom: 5px; border-radius: 5px; margin-top: 10px; margin-bottom: 10px;"
    )

def hero_section():
    return Section(
        Div(
            H1("AI-Powered Dev Environment Setup", cls="text-3xl font-bold text-center"),
            H2("From GitHub to Ready-to-Code in Seconds"),
            P("Paste your GitHub URL and get a custom devcontainer.json to simplify your development.", cls="text-lg text-center mt-4"),
            cls="container mx-auto px-4 py-16"
        ),
        cls="bg-gray-100",
    )


def generator_section():
    return Section(
        Form(
            Group(
                Input(type="text", name="repo_url", placeholder="Paste your Github repo URL, or select a repo to get started", cls="form-input", list="repo-list"),
                Datalist(
                    Option(value="https://github.com/devcontainers/templates"),
                    Option(value="https://github.com/JetBrains/devcontainers-examples"),
                    Option(value="https://github.com/devcontainers/cli"),
                    id="repo-list"
                ),
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
            H2("Benefits of Development Containers", cls="text-2xl font-bold text-center mb-8"),
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
            P("Follow these steps:", cls="text-gray-700 container mx-auto mb-4"),
            Ul(
                Li("Create a `.devcontainer/devcontainer.json` file in the root of your repository."),
                Li("Open your repository in VS Code or ",
                    A("Daytona", href="https://daytona.io", **_blank,
                        cls="border-b-2 border-b-black/30 hover:border-b-black/80"),
                   "and it will automatically run your dev container."),
                cls="list-decimal list-inside text-gray-700 mb-8"
            ),
            P("Now you're ready to develop inside your consistent and isolated dev environment!", cls="text-gray-700 container mx-auto"),
            cls="container mx-auto px-4 py-16"
        ),
    )

def manifesto():
    return Section(
        Div(
            H2("The Open Run Manifesto", cls="text-3xl font-bold text-center mb-8"),
            P("Imagine a world where any software, any code, just runs. No more complex setups. No more compatibility issues. Just pure creation.", cls="text-gray-700 container mx-auto mb-4"),
            P("Key points:", cls="text-gray-700 container mx-auto mb-4"),
            Ul(
                Li("Developers waste up to 56% of their time on environment setup and maintenance."),
                Li("Code contributions are often hindered by complicated development environments."),
                Li("We envision a future where AI handles complex setup tasks."),
                Li("Our goal: Make any code instantly runnable by anyone, anywhere."),
                cls="list-disc list-inside text-gray-700 mb-8"
            ),
            P("Join us in making instant-run software a reality for all developers.", cls="text-gray-700 container mx-auto mb-8"),
            A("Read the full manifesto",
              href="/manifesto",
              cls="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded",
              **_blank
            ),
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
            P("Experience the power of Daytona's flexible and easy development environment platform.", cls="text-lg text-center mb-6"),
            A(
                Span(
                    Img(src="assets/icons/github-mark-white.svg", cls="github-icon"),
                    "Get Daytona Now",
                    cls="button-content"
                ),
                role="button",
                href="https://github.com/daytonaio/daytona",
                target="_blank",
                title="Get Daytona",
                cls="cta-button"
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

def manifesto_page():
    return (
        Title("The Open Run Manifesto: Liberating Software for All"),
        Main(
            Section(
                Div(
                    H1("The Open Run Manifesto", cls="text-4xl font-bold text-center mb-8 text-blue-600"),
                    P("Liberating Software for All", cls="text-2xl text-gray-700 text-center mb-12"),
                    Div(
                        P("Imagine a world where any software, any code, just runs. No more complex setups. No more compatibility issues. Just pure creation.", cls="mb-4"),
                        P("We're entering an age where coding's power is accessible to all, not just developers.", cls="mb-4"),
                        P("For too long, we've accepted artificial barriers between code and execution. Developers waste nearly half of their productive time—up to 56%—just setting up and maintaining their development environments. This isn't just inefficiency; it's a creativity killer.", cls="mb-4"),
                        P("We've seen countless open source contributions and collaborative efforts stifled by complicated development environments, intricate setup processes, and the all-too-familiar \"It works on my machine\" predicament.", cls="mb-4"),
                        P("This isn't just lost time; it's lost creation.", cls="mb-4"),
                        P("No more.", cls="font-bold text-blue-600 mb-4"),
                        P("Imagine if every developer could instantly dive into coding, regardless of the project or technology stack.", cls="mb-4"),
                        P("Let's build a future where AI handles the complex task of setting up and configuring software.", cls="mb-8"),
                        cls="text-lg text-gray-700 mb-12"
                    ),
                    H3("Imagine:", cls="text-3xl font-bold mt-12 mb-6 text-blue-600"),
                    Ul(
                        Li("Checking out a repo and having it run instantly, without any manual intervention"),
                        Li("No need to read lengthy readme files or follow complex configuration steps"),
                        Li("A world where the focus is on creation, not on fighting with setup processes"),
                        cls="list-disc list-inside text-lg text-gray-700 mb-12 pl-8 space-y-2"
                    ),
                    P("Today, infrastructure-as-code configuration files offer a solution, but widespread adoption remains limited. Even among those who use them, maintenance can be inconsistent. The goal is to automate these configuration files, which simplify environment setup but are often absent or overly complex. We should make them standard for all projects globally, allowing anyone to run any code instantly.", cls="text-lg text-gray-700 mb-8"),
                    P("We are taking a first step: automating dev container creation with devcontainer.ai. This open-source initiative paves the way for a future where all code is instantly accessible and runnable by anyone, anywhere.", cls="text-lg text-gray-700 mb-8"),
                    P("We need your help to achieve this goal. Join us in making instant-run software a reality for all developers.", cls="text-xl text-gray-700 mb-8 font-bold"),
                    P("Let's build a world where code isn't just open source, but free to be used by anyone with an idea.", cls="text-lg text-gray-700 mb-12"),
                    A(
                    Span(
                            Img(src="assets/icons/github-mark-white.svg", cls="github-icon"),
                            "Contribute to devcontainer.ai",
                            cls="button-content"
                        ),
                        role="button",
                        href="https://github.com/daytonaio/devcontainer-generator",
                        target="_blank",
                        title="Get Daytona",
                        cls="cta-button"
                    ),
                    Div(
                        A("Back to Home", href="/", cls="bg-blue-500 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg text-lg"),
                        cls="mt-16 text-center"
                    ),
                    cls="container mx-auto px-8 py-16 max-w-4xl"
                ),
                cls="bg-gray-50"
            ),
            footer_section()
        )
    )