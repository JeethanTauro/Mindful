'''
cleaner basically gets the dictionary, cleans whatever is there
removes html tags, gibberish, normalises texts, handles nulls etc
nothing ever in the downstream has to worry about dirty data
'''

from bs4 import BeautifulSoup
from urllib.parse import urlparse


def remove_tags(content):
    soup = BeautifulSoup(content, "html.parser")
    # clean all the tags
    for data in soup(["script", "style"]):
        data.decompose()
    return ' '.join(soup.stripped_strings)

def normalise_whitespaces(text):
    return ' '.join(text.split())

def normalise_source(text):
    return text.lower().strip()

def valid_url(url):
    try:
        parsed = urlparse(url)
        # A valid URL should have at least scheme and netloc
        return all([parsed.scheme in ("http", "https", "ftp"), parsed.netloc])
    except Exception:
        return False

def cleaner(article_dict):
    # reject if any required field is missing or empty
    if not article_dict.get("title"):
        msg = f"REJECTED: no title — {article_dict.get('url', '')}"
        return None,msg
    if not article_dict.get("content"):
        msg = f"REJECTED: no content — {article_dict.get('url', '')}"
        return None,msg
    if article_dict.get("url") and not valid_url(article_dict.get("url")):
        msg = f"REJECTED: invalid url — {article_dict.get('url', '')}"
        return None,msg

    article_dict["content"] = remove_tags(article_dict["content"]) #first remove the tags from content
    article_dict["title"] = remove_tags(article_dict["title"]) #remove the tags from the title

    article_dict["content"] = normalise_whitespaces(article_dict["content"]) #normalise whitespaces in the content
    article_dict["title"] = normalise_whitespaces(article_dict["title"]) #normalise whitespace in the title

    article_dict["source"] = normalise_source(article_dict["source"]) #make sure the sources are normalised

    if article_dict.get("author") is None:  #making sure author is not None
            article_dict["author"] = "unknown"

    if len(article_dict.get("content", "").split()) < 100:
        return None, f"REJECTED: too short — {article_dict.get('url', 'no url')}"



    return article_dict, None


