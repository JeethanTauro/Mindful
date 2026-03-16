# career_and_productivity_writer.py
from time import sleep

from ai_writers.base_writer import BaseWriter


class CareerAndProductivityWriter(BaseWriter):
    def __init__(self):
        super().__init__()
        self.author = "ai-career-productivity-writer"
        self.model = "llama-3.3-70b-versatile"
        self.topics = [
            "how to build deep work habits",
            "the second brain method for knowledge management",
            "how top engineers approach problem solving",
            "building a personal brand as a developer",
            "how to negotiate a salary effectively",
            "the pomodoro technique and time management",
            "learning strategies that actually work"
        ]
        self.system_prompt = """
            You are a career coach and productivity expert who writes practical, 
            actionable articles grounded in research and real-world experience.
            Write articles that give readers concrete, immediately usable insights 
            about career growth and personal productivity.
            Write in 600-900 words.
            Write in plain text only — absolutely no markdown formatting.
            No headers, no bullet points, no bold, no asterisks, no hashtags.
            First line must be the article title.
            The rest must be the article body.
            Do not write 'Here is an article' or any preamble — start directly with the title.
        """
        self.category = "Career & Productivity"

def run_career_productivity_writer():
    writer = CareerAndProductivityWriter()
    writer.write_multiple("career_productivity-writer", 5)
    sleep(1)