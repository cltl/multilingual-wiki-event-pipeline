from datetime import datetime
import time
import wikipedia
import requests
import json


def get_interlanguage_links(page_names,
                            languages_of_interest={'it', 'nl'},
                            sleep=1,
                            verbose=0):
    """
    mapping of English page name to its equivalent pages in other languages
    
    :param iterable page_names: iterable of page names
    """
    en_pagename2interlanguage_links = {}

    for counter, page_name in enumerate(page_names):

        if counter % 100 == 0:
            print(counter, datetime.now())
            time.sleep(sleep)

        try:
            page = wikipedia.page(page_name)
        except (wikipedia.DisambiguationError, wikipedia.PageError):
            if verbose >= 2:
                print(f'wikipedia module was not able to find or disambiguate the page {page_name}')
            continue

        url_name = page.url.split('/')[-1]

        query = f'http://dbpedia.org/data/{url_name}.json'
        response = requests.get(query)

        try:
            data = response.json()
        except json.decoder.JSONDecodeError:
            print(f'could not decode json for {query}')
            continue

        lang2label = {}
        dbpedia_identifier = f'http://dbpedia.org/resource/{url_name}'
        label = 'http://www.w3.org/2000/01/rdf-schema#label'

        if dbpedia_identifier not in data:
            if verbose >= 2:
                print(dbpedia_identifier, 'not found in DBpedia')
            continue

        for language_info in data[dbpedia_identifier][label]:
            lang = language_info['lang']
            value = language_info['value']

            if lang in languages_of_interest:
                lang2label[lang] = value

        if not lang2label:
            if verbose >= 2:
                print(f'no interlanguage links found for {page_name}')

        en_pagename2interlanguage_links[page_name] = lang2label

    return en_pagename2interlanguage_links
