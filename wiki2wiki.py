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

languages=config.languages_list[0]
wdt_ids=['Q2635828']
obtain_wiki_page_titles(wdt_ids, languages)
