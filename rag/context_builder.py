def context_builder(chunks,metadata,enhanced_query):
    #whatever reranked chunks are there
    #and the other chunks of the retrieved chunks are also brought in
    #all of it is built togehter in one single dictionary as context and user query
    #returns the entire context built

    context_text = ""
    for i, (chunk, meta) in enumerate(zip(chunks, metadata)):
        if isinstance(meta, dict):
            title = meta.get('title')
            source = meta.get('source')
        else:
            title = meta  # fallback if something weird comes through
            source = ""
        context_text += f"\n[Source {i + 1}: '{title}' — {source}]\n{chunk}\n"

    return {
        "context": context_text,
        "query": enhanced_query
    }
