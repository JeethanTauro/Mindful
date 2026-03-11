from langchain_groq import ChatGroq

import config


def llm_chat(context,memory):
    human_message = f"""
        Context:
        {context['context']}

        Conversation history:
        {str(memory)}

        Question: {context['query']}
        """
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.4,
        streaming=True,
        api_key=config.GROQ_API_KEY
    )
    messages = [
        (
            "system",
            """You are a research assistant for Mindful, an intelligent content platform.
                   Answer the user's question based ONLY on the provided context.
                   Do not make up information. If the context lacks enough information, say so clearly.
        
                   Always respond in exactly this format:
        
                   **Answer:**
                   [Your concise, precise answer here. 2-4 paragraphs maximum.]
        
                   **Sources Used:**
                   - [Title] — [source]
                   - [Title] — [source]
        
                   Rules:
                   - Never answer outside the provided context
                   - Never list a source you didn't actually use in your answer
                   - If context is insufficient, just write: "The available articles don't cover this topic in enough detail."
                   - Keep answers focused and direct — no filler, no repetition
                   """
        ),
        (
            "human",
            human_message
        )
    ]
    llm_output = llm.invoke(messages)
    return llm_output.content

