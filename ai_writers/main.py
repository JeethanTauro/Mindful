import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from ai_writers.finance.deep_finance_knowledge_writer import run_deep_finance_knowledge_writer
from ai_writers.finance.latest_finance_writer import run_latest_finance_writer
from ai_writers.soceity.career_and_productivity_writer import run_career_productivity_writer
from ai_writers.soceity.human_psychology_writer import run_human_psychology_writer
from ai_writers.soceity.societyAndWorldViewWriter import run_society_world_view_writer
from tech.system_design_writer import run_system_design_write
from tech.casestudy_writer import run_tech_case_study_write
from tech.latest_news_writer import run_latest_tech_news_write


ai_writers = [
    "system_design_writer",
    "latest_tech_news_writer",
    "case_study_writer",
    "society_worldview_writer",
    "human_psychology_writer",
    "latest_finance_writer",
    "deep_finance_writer",
    "career_productivity_writer",
    ]

def run_ai_writer(ai_writer_name):
    if ai_writer_name == "system_design_writer":
        run_system_design_write()
    elif ai_writer_name == "latest_tech_news_writer":
        run_latest_tech_news_write()
    elif ai_writer_name == "case_study_writer":
        run_tech_case_study_write()
    elif ai_writer_name == "society_worldview_writer":
        run_society_world_view_writer()
    elif ai_writer_name == "human_psychology_writer":
        run_human_psychology_writer()
    elif ai_writer_name == "latest_finance_writer":
        run_latest_finance_writer()
    elif ai_writer_name == "deep_finance_writer":
        run_deep_finance_knowledge_writer()
    elif ai_writer_name == "career_productivity_writer":
        run_career_productivity_writer()

    return None

if __name__ == "__main__":
    initial_time = datetime.now()
    random.shuffle(ai_writers) #shuffle the order of submission
    with ThreadPoolExecutor(max_workers=8) as executor:
        '''
        see we can have a list of future too like future = [executor.submit(run_spider,spider) for spider in spiders]but it would be nice to have 
        {future : name of the spider} in a dictionary forma t
        '''
        futures = {executor.submit(run_ai_writer, ai_writer):
                       ai_writer for ai_writer in
                   ai_writers}  # run_ai_writer is the function name to run, ai_writer is the argument given
        for future in as_completed(futures):
            writer_name = futures[future]
            try:
                result = future.result()  # Blocks until the task finishes
                print(f"{writer_name} completed : {result}")
            except Exception as exc:
                print(f"{writer_name} failed : {exc}")

    final_time = datetime.now()

    elapsed = final_time - initial_time
    print(f"Total time elapsed : {elapsed}")
