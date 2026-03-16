from time import sleep

from ai_writers.base_writer import BaseWriter

# deep_finance_knowledge_writer.py
class DeepFinanceKnowledgeWriter(BaseWriter):
    def __init__(self):
        super().__init__()
        self.author = "ai-deep-finance-writer"
        self.model = "llama-3.3-70b-versatile"
        self.topics = [
            "how compound interest works",
            "understanding options trading",
            "what is quantitative easing",
            "how hedge funds operate",
            "the mechanics of short selling",
            "how central banks control inflation",
            "understanding the yield curve",
            "what drives currency exchange rates",
            "how IPOs work"
        ]
        self.system_prompt = """
            You are a senior financial analyst and educator who explains complex 
            financial concepts in clear, accessible language for a general audience.
            Write deep, well-researched explanatory articles that give readers 
            genuine understanding of financial mechanisms and concepts.
            Write in 600-900 words.
            Write in plain text only — absolutely no markdown formatting.
            No headers, no bullet points, no bold, no asterisks, no hashtags.
            First line must be the article title.
            The rest must be the article body.
            Do not write 'Here is an article' or any preamble — start directly with the title.
        """
        self.category = "Finance & Economics"

def run_deep_finance_knowledge_writer():
    writer = DeepFinanceKnowledgeWriter()
    writer.write_multiple("deep_finance-writer", 5)
    sleep(1)