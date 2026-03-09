from time import sleep

from ai_writers.base_writer import BaseWriter

class LatestTechNewsWriter(BaseWriter):
    def __init__(self):
        super().__init__()
        self.author = "ai-latest-tech-news-writer"
        self.topics = ["Electric Vehicles","Artificial Intelligence","Agentic AI","Machine Learning","Quantum Computing","Military","Gadgets","Microsoft","Apple","Google","Anthropic","Meta"]
        self.model = "groq/compound"
        self.system_prompt = """
                                You are an enthusiastic tech reviewer who checks on the latest techs released
                                recently around the globe
                                Write clear, concise news articles
                                Write in 600-900 words
                                Write in plain text only — absolutely no markdown formatting.No headers, no bullet points, no bold, no asterisks, no hashtags.
                                First line must be the article title.   
                                The rest must be the article body.
                                Do not write 'Here is an article' or any preamble — start directly with the title.
                            """ #system prompt to write on system design and tech stuff
        self.category = "Tech News"


#this is the method that creates the object and then calls the writer method
def run_latest_tech_news_write():
    n = 5
    latest_tech_news_writer = LatestTechNewsWriter()
    latest_tech_news_writer.write_multiple("latest_tech_news-writer", 5)
    sleep(1)


