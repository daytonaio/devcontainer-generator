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
                embedding = openai_client.embeddings.create(input=repo_context, model=os.getenv("EMBEDDING")).data[0].embedding
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