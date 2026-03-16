# human_psychology_writer.py
from time import sleep

from ai_writers.base_writer import BaseWriter


class HumanPsychologyWriter(BaseWriter):
    def __init__(self):
        super().__init__()
        self.author = "ai-human-psychology-writer"
        self.model = "llama-3.3-70b-versatile"
        self.topics = [
            "cognitive biases that affect decision making",
            "the psychology behind social media addiction",
            "how dopamine drives human behavior",
            "the dunning kruger effect in the workplace",
            "why humans fear change and how to overcome it",
            "the psychology of procrastination",
            "how confirmation bias shapes our worldview",
            "the science of habit formation"
        ]
        self.system_prompt = """
            You are a behavioral psychologist and science writer who explains 
            human psychology in clear, accessible language.
            Write engaging articles that connect psychological research to 
            everyday human behavior and experiences.
            Write in 600-900 words.
            Write in plain text only — absolutely no markdown formatting.
            No headers, no bullet points, no bold, no asterisks, no hashtags.
            First line must be the article title.
            The rest must be the article body.
            Do not write 'Here is an article' or any preamble — start directly with the title.
        """
        self.category = "Human Psychology"

def run_human_psychology_writer():
    writer = HumanPsychologyWriter()
    writer.write_multiple("human_psychology-writer", 5)
    sleep(1)