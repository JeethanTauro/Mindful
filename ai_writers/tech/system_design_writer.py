from time import sleep

from ai_writers.base_writer import BaseWriter

class SystemDesignWriter(BaseWriter):
    def __init__(self):
        super().__init__()
        self.author = "ai-system-design-writer"
        self.topics = ["distributed systems","caching","microservices","monoliths","event driven architecture","scalable systems","fault tolerance","SOLID principles","Design Patterns","Programming languages Quirks"]
        self.model = "llama-3.3-70b-versatile"
        self.system_prompt = """
                                You are a senior software architect and system design engineer writing technical articles.
                                Write clear, concise system design articles
                                Write in 600-900 words
                                Write in plain text only — absolutely no markdown formatting.No headers, no bullet points, no bold, no asterisks, no hashtags.
                                First line must be the article title.   
                                The rest must be the article body.
                                Do not write 'Here is an article' or any preamble — start directly with the title.
                            """ #system prompt to write on system design and tech stuff
        self.category = "System Design"


#this is the method that creates the object and then calls the writer method
def run_system_design_write():
    system_design_writer = SystemDesignWriter()
    system_design_writer.write_multiple("system-design-writer",5)
    sleep(1)

