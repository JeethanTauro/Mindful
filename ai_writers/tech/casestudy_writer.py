from time import sleep

from ai_writers.base_writer import BaseWriter

class TechCaseStudyWriter(BaseWriter):
    def __init__(self):
        super().__init__()
        self.author = "ai-tech-case-study-writer"
        self.topics = ["Netflix","Uber","Instagram","Facebook","Youtube","Google","LLMs"]
        self.model = "groq/compound"
        self.system_prompt = """
                                You are a senior software developer who understands how big and large scalable systems work
                                Write clear, concise case study and internal working of different segments in the company articles
                                Write in 600-900 words
                                Write in plain text only — absolutely no markdown formatting.No headers, no bullet points, no bold, no asterisks, no hashtags.
                                First line must be the article title.   
                                The rest must be the article body.
                                Do not write 'Here is an article' or any preamble — start directly with the title.
                            """ #system prompt to write on system design and tech stuff
        self.category = "Tech Case Study"


#this is the method that creates the object and then calls the writer method
def run_tech_case_study_write():
    n=5
    tech_case_study_writer = TechCaseStudyWriter()
    tech_case_study_writer.write_multiple("tech_case_study-writer", 5)
    sleep(1)

