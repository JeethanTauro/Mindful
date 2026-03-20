import datetime
from ingestion.lake_writer import upload
from concurrent.futures import ThreadPoolExecutor,as_completed
from spiders import hackernews, arxiv_spider, wikipedia_spider

#list of the spider names
spiders = ["arxiv_spider", "hackernews_spider", "wikipedia_spider"]

#runs entire arxiv spider from start to finish
def arxiv_spider_run():
    results  = arxiv_spider.fetch_content()
    list_raw_articles = arxiv_spider.map_to_schema(results)
    upload(list_raw_articles,"arxiv")
    return len(list_raw_articles)

#runs entire hackernews spider from start to finish
def hackernews_spider_run():
    ids = hackernews.fetch_ids()
    results = hackernews.flatten_list_ids(ids)
    list_raw_articles = hackernews.hit_item_endpoint(results)
    upload(list_raw_articles,"hackernews")
    return len(list_raw_articles)


#runs entire wikipedia spider from start to finsh
def wikipedia_spider_run():
    list_of_pages = wikipedia_spider.fetch_pages()[:15]
    list_raw_articles = wikipedia_spider.map_to_schema(list_of_pages)
    upload(list_raw_articles,"wikipedia")
    return len(list_raw_articles)

def run_spider(spider_name_):
    if spider_name_ == "arxiv_spider":
        return arxiv_spider_run()
    elif spider_name_ == "hackernews_spider":
        return hackernews_spider_run()
    elif spider_name_ == "wikipedia_spider":
        return wikipedia_spider_run()
    return None


if __name__ == "__main__":
    initial_time = datetime.datetime.now()
    with ThreadPoolExecutor(max_workers=3) as executor:
        '''
        see we can have a list of future too like future = [executor.submit(run_spider,spider) for spider in spiders]but it would be nice to have 
        {future : name of the spider} in a dictionary forma t
        '''
        futures = {executor.submit(run_spider,spider):
                       spider for spider in spiders}#run spider is the function name to run, spider is the argument given
        for future in as_completed(futures):
            spider_name = futures[future]
            try:
                result = future.result()# Blocks until the task finishes
                print(f"{spider_name} completed : {result}")
            except Exception as exc:
                print(f"{spider_name} failed : {exc}")

    final_time = datetime.datetime.now()

    elapsed = final_time - initial_time
    print(f"Total time elapsed : {elapsed}")
