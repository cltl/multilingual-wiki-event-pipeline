import requests

def obtain_date_of_creation(titles, language):

    title_filter='|'.join(titles)
    dates={}
    params={
            'action': 'query',
            'prop': 'revisions',
            'rvlimit': 1,
            'rvprop': 'timestamp',
            'rvdir': 'newer',
            'titles': title_filter,
            'format': 'json'
            }
    url='https://%s.wikipedia.org/w/api.php?' % language
    r=requests.get(url, params=params)
    json_response=r.json()
    print(titles, json_response)
    for page_id, page_info in json_response['query']['pages'].items():
        dates[page_info['title']]=page_info['revisions'][0]['timestamp']

    return dates

def map_user_to_uri(user, lang):
    return 'https://%s.wikipedia.org/wiki/User:%s' % (lang, user.replace(' ', '_'))

def obtain_contributors(titles, language):
    title_filter='|'.join(titles)
    contributors={}
    params={
            'action': 'query',
            'titles': title_filter,
            'prop': 'contributors',
            'format': 'json'
            }
    url='https://%s.wikipedia.org/w/api.php?' % language
    r=requests.get(url, params=params)
    print(r.url)
    json_response=r.json()
    for page_id, page_info in json_response['query']['pages'].items():
        c=[]
        print(page_info)
        for contributor in page_info['contributors']:
            c.append(map_user_to_uri(contributor['name'], language))
        contributors[page_info['title']]=c
    return contributors

def obtain_wiki_page_titles(wdt_ids, languages):

    ids_filter='|'.join(wdt_ids)
    languages_filter='|'.join(list(map(lambda x: x + 'wiki', languages)))
    params={
            'action': 'wbentities',
            'props': 'sitelinks',
            'ids': ids_filter,
            'sitefilter': languages_filter,
            'format': 'json'
            }
    url='https://www.wikidata.org/w/api.php?'
    r=requests.get(url, params=params)
    j=r.json()
    # f = urllib.request.urlopen(url)
    # j=json.loads(f.read().decode('utf-8'))

    results_batch={}
    if 'entities' in j.keys():
        for id, id_data in j['entities'].items():
            results_one={}
            sitelinks=id_data['sitelinks']
            for sitelink, data in sitelinks.items():
                results_one[data['site'][:2]]=data['title']
            if len(results_one.keys()):
                results_batch[id]=results_one
    print(len(results_batch))
    return results_batch

def filter_langlinks(a_list, other_l):
    a_dict={}
    for elem in a_list:
        lang=elem['lang']
        if lang in other_l:
            a_dict[lang]=elem['*']
    return a_dict

def adapt_extlinks(a_list):
    out_list=[]
    for element in a_list:
        for k,v in element.items():
            out_list.append(v)
    return out_list
    

def obtain_wiki_page_info(title, lang, props, extract_text=True, other_languages=set()):
    params={
            'format': 'json',
            'action': 'query',
            'prop': '|'.join(props),
            'explaintext': extract_text,
            'titles': title,
            'redirects': True,
            'exlimit': 1
            }
    url='https://%s.wikipedia.org/w/api.php?' % lang
    r=requests.get(url, params=params)
    j=r.json()
    print(j)
    data={}
    for page_id, page_info in j['query']['pages'].items():
        if page_id=='-1': continue
        data['title']=page_info['title']
        data['extract']=page_info['extract']
        for p in props:
            if p in page_info.keys():
                if p=='langlinks':
                    data[p]=filter_langlinks(page_info[p], other_languages)
                elif p=='extlinks':
                    data[p]=adapt_extlinks(page_info[p])
                else:
                    data[p]=page_info[p]
    print('RETURNING', data)
    return data


#d=obtain_date_of_creation(title, lang)
#c=obtain_contributors(title, lang)
#print(c, d)
