import json
import urllib.request
import urllib.parse

import config


def obtain_wiki_page_titles(wdt_ids, languages):

    ids_filter='|'.join(wdt_ids)
    languages_filter='|'.join(list(map(lambda x: x + 'wiki', languages)))
    url='https://www.wikidata.org/w/api.php?action=wbgetentities&format=xml&props=sitelinks&ids=%s&sitefilter=%s&format=json' % (ids_filter, languages_filter)
    print(url)
    f = urllib.request.urlopen(url)
    j=json.loads(f.read().decode('utf-8'))
    print(j)
    for id, id_data in j['entities'].items():
        sitelinks=id_data['sitelinks']
        for sitelink, data in sitelinks.items():
            print(data['site'], data['title'])

def split_in_batches(a_list, batch_size=500):
    """Yield successive n-sized chunks from a_list."""
    for i in range(0, len(a_list), batch_size):
        yield a_list[i:i + batch_size]

test_list=list(range(10, 75))
for iter in split_in_batches(test_list, 10):
    print(iter)

languages=config.languages_list[0]
wdt_ids=['Q2635828']
obtain_wiki_page_titles(wdt_ids, languages)
