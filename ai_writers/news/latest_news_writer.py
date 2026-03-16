from time import sleep

from ai_writers.base_writer import BaseWriter

# latest_news_writer.py
class LatestNewsWriter(BaseWriter):
    def __init__(self):
        super().__init__()
        self.author = "ai-latest-news-writer"
        self.model = "compound-beta"   # compound-beta has live web search
        self.topics = [
            "artificial intelligence",
            "tech industry",
            "startups and venture capital",
            "cybersecurity",
            "semiconductor industry",
            "big tech regulation",
            "open source software"
        ]
        self.system_prompt = """
            You are a technology journalist who writes sharp, informative news articles
            about the latest developments in tech and AI.
            Search the web for the most recent news on the given topic and write 
            a well-structured news article about it.
            Write in 600-900 words.
            Write in plain text only — absolutely no markdown formatting.
            No headers, no bullet points, no bold, no asterisks, no hashtags.
            First line must be the article title.
            The rest must be the article body.
            Do not write 'Here is an article' or any preamble — start directly with the title.
        """
        self.category = "Latest News"

def run_latest_news_writer():
    writer = LatestNewsWriter()
    writer.write_multiple("latest_news-writer", 5)
    sleep(1)