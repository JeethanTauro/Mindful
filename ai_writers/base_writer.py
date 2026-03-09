'''
every writer does the same 3 things:
1) call the API
2) schema mapping to RawArticle
3) upload it to minio
'''
import uuid

import config
from groq import Groq
import random
from ingestion.schema import RawArticle
from datetime import datetime
from ingestion.lake_writer import upload

class BaseWriter:
    def __init__(self):
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.author = None #child will define this
        self.model =None #child will define this
        self.topics = [] #child will define this
        self.system_prompt = "" #child will define this
        self.category = ""
    def call_api(self,topic): #call the groq api
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": self.system_prompt,
                },
                {
                    "role": "user",
                    "content": f"Write an article on a specific and unique aspect of {topic}.Choose an angle that is not commonly covered.",
                }
            ],

            model=self.model
        )
        return chat_completion,topic

    def parse_response(self, raw_text,topic):# extract title and content from response
        lines = raw_text.strip().split('\n')
        title = lines[0].replace("Title:", "").strip() #the first line of the raw text will be title
        content = '\n'.join(lines[1:]).strip() #the rest is content
        return {
            "title": title,
            "content":content,
            "topic":topic
        }


    def schema_mapping_to_raw(self, parsed_dict):
        return RawArticle(
            source_id=str(uuid.uuid4()),
            source = "ai_generated",
            url=f"https://ai.generated/{self.author}/{str(uuid.uuid4())}",
            title=parsed_dict["title"],
            author=self.author,
            content=parsed_dict["content"],
            tags=[self.category, self.author, parsed_dict["topic"]],
            published_at=datetime.now()
        )

    def upload_ai_article(self,article,name):
        upload(list_raw_articles=[article],spider=name)

    #ties it all together
    def write_multiple(self, name, n=5):  # multiple articles, no topic repetition
        topics = random.sample(self.topics, min(n, len(self.topics)))
        for topic in topics:
            response, topic = self.call_api(topic)
            text = response.choices[0].message.content
            parsed = self.parse_response(text, topic)
            article = self.schema_mapping_to_raw(parsed)
            self.upload_ai_article(article, name)
            print(f"[{self.author}] Written article on: {topic}")

