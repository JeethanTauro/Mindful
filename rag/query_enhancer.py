#looking at the history of the conversation the query must be enhanced
from langchain_groq import ChatGroq

import config


def enhancer(query,memory):
    #we take in the user query
    #take in the history from the chat
    #make an API call to the LLM
    #tell the llm to construct the query in a better manner looking at the chat history
    #return the enhanced query
    if not memory:
        return query  # no history, no rewriting needed

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0,api_key=config.GROQ_API_KEY)
    messages = [
        ("system", """You are a query rewriter. Given a conversation history and a follow-up question,
             rewrite the follow-up question to be a complete standalone question that captures the full intent.
             Return ONLY the rewritten question, nothing else."""),
        ("human", f"""
             Conversation history: {str(memory)}
             Follow-up question: {query}
             Rewritten standalone question:""")
    ]
    result = llm.invoke(messages)
    return result.content.strip()
