#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Ingestion

Download wikipedia pages for numerous programming languages and save it to a database.
If the entry is a certain amount different than the existing copy, update the stored record.
"""

from datetime import datetime
from difflib import SequenceMatcher
import pandas as pd
import requests
import json
from collections import namedtuple
import wrappers.storage_wrapper as stor


def make_name_title_dict():
    """ Ingest spreadsheet and create dictionary holding the PL name and it's wikipedia page title """
    df = pd.read_csv("./data/All_Programming_Languages.csv")
    names = [t.rsplit('/', 1)[-1].lower() for t in df.ProgrammingLanguage]
    titles = [t.rsplit('/', 1)[-1] for t in df.Source]

    # The source csv has over 600 languages, but we are not interested in all of them.
    # Pre-filter what goes into the dictionary so that it is more relevant and
    # wieldy.
    list_langs_to_keep = ["C++", "Bash", "Java", "C#", "Rust", "Go", "Python",
                          "Javascript", "R", "Julia", "Php", "Scala", "Ruby",
                          "F#", "Fortran", "Matlab", "Elixir", "Clojure", "Kotlin"]

    name_to_page_title = {}
    for name, title in zip(names, titles):
        if name.strip().title() not in list_langs_to_keep:
            continue
        name_to_page_title.update({name: title})

    assert len(name_to_page_title.keys()) == len(list_langs_to_keep)
    return name_to_page_title


def clean_raw_record(text):
    """ Return useful text from raw wiki result or return an error.
        On error, return early with False as the second entry of the tuple"""

    # Drill down from total json response to the article text
    lang_entry_as_json = None
    try:
        lang_entry_as_json = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"Exception occurred {e.with_traceback()}")
        return None, False
    json_obj = lang_entry_as_json
    # All json objects have the key 'query'
    assert 'query' in json_obj.keys()
    query_content = json_obj['query']
    # All 'query' entries have the key 'pages'
    assert 'pages' in query_content.keys()
    num_pages = len(query_content['pages'].keys())
    # All 'pages' entries have a single page
    assert num_pages == 1
    key_name_for_page = list(query_content['pages'].keys())[0]
    meaningful_text_content = query_content['pages'][key_name_for_page]
    # Skip langs that have a '-1' as their page id, because these
    # entries do not have any data
    if key_name_for_page == '-1':
        return None, False
    assert 'revisions' in meaningful_text_content.keys()

    text = meaningful_text_content['revisions'][0]['*']
    return text, True


def query_wiki_api_for_latest():
    """ Generator for entries in the wiki api. """
    name_to_title = make_name_title_dict()
    skipped_for_bad_request_result = []

    for name, article_title in name_to_title.items():
        query = fr"https://en.wikipedia.org/w/api.php?action=query&titles={article_title}&prop=revisions&rvprop=content&format=json"
        try:
            result = requests.get(query)
        except Exception as e:
            skipped_for_bad_request_result.append(name)
            print(f"Exception occurred {e.with_traceback()}")
            continue

        text_to_save = clean_raw_record(result.text)

        if not result.ok or len(result.text) < 3:
            print(f"Unusable result for language {name}, skipping")
            skipped_for_bad_request_result.append(name)
            continue

        # Create return value
        usable_text, ok = clean_raw_record(result.text)
        if ok == False:
            continue

        ret_val = namedtuple("LangEntry", ["name", "json_text"])
        yield ret_val(name=name.strip(), json_text=usable_text)


def update_cache_if_newer(wrapper):
    """ Update local shelf file entries if the new entry is less
    than a threshold similar in content """
    ARTICLE_SIMILARITY_CUTOFF = 0.99
    # Store the entries that we update so that we can use it later
    updated = []
    todays_date = datetime.today().date()
    for lang_entry in query_wiki_api_for_latest():
        if lang_entry.name in wrapper.keys():

            # Load entry from database
            stored_json, stored_date = wrapper.find(lang_entry.name)

            seq_diff = SequenceMatcher(None, lang_entry.json_text, stored_json)
            ratio = seq_diff.quick_ratio()
            if ratio >= ARTICLE_SIMILARITY_CUTOFF:
                print(f"{lang_entry.name} entry was not newer than saved copy")
                continue
            else:
                print(
                    f"Meaningful difference of {ratio} found for {lang_entry.name}")
                wrapper.insert_or_update(
                    lang_entry.name, lang_entry.json_text, todays_date)
                continue
        else:
            print(f"{lang_entry.name} was not in cache. Adding it now")
            # Save new entry to database
            wrapper.insert_or_update(
                lang_entry.name, lang_entry.json_text, todays_date)


if __name__ == "__main__":
    QUERY_ENDPOINT_FOR_UPDATES = True
    wrapper = stor.StorageWrapper("prod")
    wrapper.open_or_create("languages")
    if QUERY_ENDPOINT_FOR_UPDATES:
        update_cache_if_newer(wrapper)
