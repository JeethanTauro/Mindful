from datetime import datetime
from time import sleep
import trafilatura
import requests
import config
from ingestion.lake_writer import upload
from ingestion.schema import RawArticle
'''
first hit the api -> get 1000 ids
for each id:
    first inject it in the params of the item endpoint to get the details
    filter out the non story type because hacker news has , ask, poll, job, comment (this we can do using type)
        if it has text-> just take it as the content
        if it has url -> go to the url and then scrape the content using trafilatura
        if neither then skip the article
    handle the fetch failures gracefully using try except
    map to RawArticle
    sleep for 1 second (so that we respect the rate limiting)
now we have all the raw article objects
one by one write them to the raw bucket in minio and then publish event to stream
'''

#fetching the top and new stories and returning them in a list of lists
def fetch_ids():
    r_top_stories = requests.get(config.HACKER_TOP_STORIES)
    r_new_stories = requests.get(config.HACKER_NEW_STORIES)

    return [r_top_stories.json(), r_new_stories.json()]

#flatten the list of list and return the list of all ids
def flatten_list_ids(ids):

    list_ids = [item for sublist in ids for item in sublist]
    return list_ids

#build the item endpoint and for each id hit that endpoint
def hit_item_endpoint(list_ids):
    seen_ids = set()
    list_raw_articles = []
    item_endpoint = config.HACKER_NEWS_ITEM
    for id in list_ids:
        url = ""
        content=""
        title = ""
        author = ""
        if id not in seen_ids:
            seen_ids.add(id)
            endpoint = item_endpoint + f"{id}.json?print=pretty"
            #try to hit the endpoint
            try:
                r = requests.get(endpoint)
                if r.status_code == 200:
                    r = r.json()
                    #can be text or url but it has to be a story
                    if (r.get("text","") != "" or r.get("url","") != "") and r.get("type")=="story":
                        author = r.get("by","")
                        title = r.get("title","")
                        content  = r.get("text","")
                        # use trafilatura and get the content
                        if content == "":
                            url = r.get("url","")
                            try:
                                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                                response = requests.get(url, headers=headers, timeout=10)
                                content = trafilatura.extract(response.text) or ""

                            except Exception as e:
                                print(e)
                            if content == "":
                                continue


                    #if both text and url are not there then skip this article id
                    else:
                        continue

                    raw = RawArticle(source_id= str(r.get("id", "")),source="hackernews", url=url, title=title, author=author, content=content, tags=["hackernews"],
                             published_at=datetime.fromtimestamp(r["time"]) if r.get("time") else None)
                    list_raw_articles.append(raw)
                    sleep(1)
            except requests.exceptions.RequestException as e:
                print(e)
    return  list_raw_articles




if __name__ == "__main__":
    ids = fetch_ids() #fech ids
    print("fetched ids",ids)
    print("\n")
    list_ids = flatten_list_ids(ids)[:5]
    print("flattened the list",list_ids)
    print("\n")
    list_raw_articles =  hit_item_endpoint(list_ids)
    print("List of raw articles",list_raw_articles)
    print("\n")
    upload(list_raw_articles,"hackernews")
    print("Uploaded it in minio by hackernews spider")




