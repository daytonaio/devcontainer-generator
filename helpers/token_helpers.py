import tiktoken

def count_tokens(text):
    encoder = tiktoken.encoding_for_model("gpt-4o")
    tokens = encoder.encode(text)
    return len(tokens)

def truncate_to_token_limit(text, model_name, max_tokens):
    encoding = tiktoken.encoding_for_model(model_name)
    tokens = encoding.encode(text)
    if len(tokens) > max_tokens:
        truncated_tokens = tokens[:max_tokens]
        return encoding.decode(truncated_tokens)
    return text