import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from tech.system_design_writer import run_system_design_write
from tech.casestudy_writer import run_tech_case_study_write
from tech.latest_news_writer import run_latest_tech_news_write


ai_writers = ["system_design_writer", "latest_tech_news_writer", "case_study_writer"]

def run_ai_writer(ai_writer_name):
    if ai_writer_name == "system_design_writer":
        run_system_design_write()
    elif ai_writer_name == "latest_tech_news_writer":
        run_latest_tech_news_write()
    elif ai_writer_name == "case_study_writer":
        run_tech_case_study_write()
    return None

if __name__ == "__main__":
    initial_time = datetime.now()
    random.shuffle(ai_writers) #shuffle the order of submission
    with ThreadPoolExecutor(max_workers=3) as executor:
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
