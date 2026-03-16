from langchain_groq import ChatGroq

import config

llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        streaming=True,
        api_key=config.GROQ_API_KEY
    )
def casual_query(query,memory):
    messages = [
        (
            "system",
            """
            -You are an AI assistant for "Mindful", "Mindful" is a website that contains articles which users can read and it also has a chatbot
            -Make sure you answer the user in a few lines only
            -You can only answer casual questions regarding "Mindful" and nothing else
            -You are strictly forbidden from replying more than 3 lines and anything else other than "Mindful"
            """
        ),
        (
            "human",
            f"""
            Conversational memory : {memory}
            User Query : {query}
            """
        )
    ]
    llm_output = llm.invoke(messages)
    return {"answer": llm_output.content, "safe": True, "sources":[]}