from time import sleep

from ai_writers.base_writer import BaseWriter

# latest_finance_writer.py
class LatestFinanceWriter(BaseWriter):
    def __init__(self):
        super().__init__()
        self.author = "ai-latest-finance-writer"
        self.model = "compound-beta"   # compound-beta for live market news
        self.topics = [
            "stock market",
            "cryptocurrency",
            "global economy",
            "central bank policy",
            "venture capital",
            "fintech industry",
            "emerging markets"
        ]
        self.system_prompt = """
            You are a financial journalist who writes clear, accurate articles about 
            the latest developments in finance and markets.
            Search the web for the most recent news on the given topic and write 
            a well-structured finance news article about it.
            Write in 600-900 words.
            Write in plain text only — absolutely no markdown formatting.
            No headers, no bullet points, no bold, no asterisks, no hashtags.
            First line must be the article title.
            The rest must be the article body.
            Do not write 'Here is an article' or any preamble — start directly with the title.
        """
        self.category = "Finance News"

def run_latest_finance_writer():
    writer = LatestFinanceWriter()
    writer.write_multiple("latest_finance-writer", 5)
    sleep(1)