# society_world_view_writer.py
from time import sleep

from ai_writers.base_writer import BaseWriter


class SocietyAndWorldViewWriter(BaseWriter):
    def __init__(self):
        super().__init__()
        self.author = "ai-society-worldview-writer"
        self.model = "llama-3.3-70b-versatile"
        self.topics = [
            "how social media is reshaping human attention spans",
            "the psychology of viral content",
            "how urbanization is changing social behavior",
            "the rise of digital loneliness",
            "how misinformation spreads online",
            "the impact of remote work on society",
            "cancel culture and public accountability"
        ]
        self.system_prompt = """
            You are a thoughtful social analyst and writer who explores how technology 
            and modern systems shape human society and worldviews.
            Write clear, insightful articles that connect technology trends to real 
            human and societal impact.
            Write in 600-900 words.
            Write in plain text only — absolutely no markdown formatting. 
            No headers, no bullet points, no bold, no asterisks, no hashtags.
            First line must be the article title.
            The rest must be the article body.
            Do not write 'Here is an article' or any preamble — start directly with the title.
        """
        self.category = "Society & Worldview"

def run_society_world_view_writer():
    writer = SocietyAndWorldViewWriter()
    writer.write_multiple("society_worldview-writer", 5)
    sleep(1)