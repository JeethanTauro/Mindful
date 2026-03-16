from langchain_groq import ChatGroq

import config

llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        streaming=False,
        api_key=config.GROQ_API_KEY
    )
def router(query):
    messages = [
        (
            "system",
            """
            -You are a query analyser, Your job is to analyse the user query and understand whther the query is for RAG (retrieval augmented generation)
            or just a casual query.
            -Your job is to return only ONE word and ONE word only either RAG_QUERY or CASUAL_QUERY
            -If the query by the user is for RAG then return RAG_QUERY else return CASUAL_QUERY
            Examples:
            "hi" → CASUAL_QUERY
            "what is this website" → CASUAL_QUERY
            "what is mindful about"-> CASUAL_QUERY
            "thanks" → CASUAL_QUERY
            "who are you" → CASUAL_QUERY
            "explain how Netflix uses caching" → RAG_QUERY
            "tell me about distributed systems" → RAG_QUERY
            "what is machine learning" → RAG_QUERY
            "how does Google search work" → RAG_QUERY
            -You are strictly forbidden from returning anything else
            """
        ),
        (
            "human",
            query
        )
    ]
    llm_output = llm.invoke(messages)
    return llm_output.content.strip()