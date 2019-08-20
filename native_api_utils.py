import requests

def obtain_date_of_creation(titles, language):
    """
    Obtain date of creation for a number of documents.
    """
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
    for page_id, page_info in json_response['query']['pages'].items():
        dates[page_info['title']]=page_info['revisions'][0]['timestamp']

    return dates

def map_user_to_uri(user, lang):
    """Map Wikipedia contributor/user from a username to a URI."""
    return 'https://%s.wikipedia.org/wiki/User:%s' % (lang, user.replace(' ', '_'))

def obtain_contributors(titles, language):
    """Obtain contributors for a set of Wikipedia titles."""
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
    json_response=r.json()
    for page_id, page_info in json_response['query']['pages'].items():
        c=[]
        for contributor in page_info['contributors']:
            c.append(map_user_to_uri(contributor['name'], language))
        contributors[page_info['title']]=c
    return contributors

def obtain_wiki_page_titles(wdt_ids, languages):
    """Obtain Wikipedia page titles from a set of Wikidata IDs."""
    ids_filter='|'.join(wdt_ids)
    languages_filter='|'.join(list(map(lambda x: x + 'wiki', languages)))
    params={
            'action': 'wbgetentities',
            'props': 'sitelinks',
            'ids': ids_filter,
            'sitefilter': languages_filter,
            'format': 'json'
            }
    url='https://www.wikidata.org/w/api.php?'
    r=requests.get(url, params=params)
    j=r.json()
    results_batch={}
    if 'entities' in j.keys():
        for id, id_data in j['entities'].items():
            results_one={}
            sitelinks=id_data['sitelinks']
            for sitelink, data in sitelinks.items():
                results_one[data['site'][:2]]=data['title']
            if len(results_one.keys()):
                results_batch[id]=results_one
    return results_batch

def filter_langlinks(a_list, other_l):
    """Filter the langlinks based on a list of languages of interest."""
    a_dict={}
    for elem in a_list:
        lang=elem['lang']
        if lang in other_l:
            a_dict[lang]=elem['*']
    return a_dict

def adapt_extlinks(a_list):
    """Simplify the structure of the extlinks dictionary."""
    out_list=[]
    for element in a_list:
        for k,v in element.items():
            out_list.append(v)
    return out_list
    
def obtain_results_from_api(url, params):
    try:
        r=requests.get(url, params=params)
    except:
        print('Error with wikipage', url, params)
        return {}
    j=r.json()
    if 'batchcomplete' not in j.keys() and 'parse' not in j.keys():
        print(r.request.url)
    return j

def obtain_primary_rt_links(title, lang):

    params_extlinks={
            'format': 'json',
            'action': 'query',
            'prop': 'extlinks',
            'titles': title,
            'redirects': True,
            'ellimit': 500
            }

    url='https://%s.wikipedia.org/w/api.php?' % lang

    j_el=obtain_results_from_api(url, params_extlinks)
    if 'query' not in el.keys(): 
        print('no query for this page')
        return []

    for page_id, page_info in j_el['query']['pages'].items():
        if page_id=='-1': continue

        if 'extlinks' in page_info.keys():
            els=adapt_extlinks(page_info['extlinks'])
            return els
    return []

def obtain_wiki_page_info(title, lang, props, extract_text=True, other_languages=set()):
    """Obtain information for a Wikipedia page title. The requested pieces of information are defined in the `props` parameter."""
    params_extracts={
            'format': 'json',
            'action': 'query',
            'prop': 'extracts',
            'explaintext': extract_text,
            'titles': title,
            'redirects': True,
            'exlimit': 1,
            }
    params_extlinks={
            'format': 'json',
            'action': 'query',
            'prop': 'extlinks',
            'titles': title,
            'redirects': True,
            'ellimit': 500
            }
    params_langlinks={
            'format': 'json',
            'action': 'query',
            'prop': 'langlinks',
            'titles': title,
            'redirects': True,
            'lllimit': 500
            }
    params_wikitext={
            'format': 'json',
            'action': 'parse',
            'prop': 'wikitext',
            'page': title,
            'section': 0
    }
    url='https://%s.wikipedia.org/w/api.php?' % lang

    j=obtain_results_from_api(url, params_extracts)
    data={}
    for page_id, page_info in j['query']['pages'].items():
        if page_id=='-1': continue
        data['title']=page_info['title']
        if 'extract' in page_info.keys():
            data['extract']=page_info['extract']

        j_el=obtain_results_from_api(url, params_extlinks)
        if page_id in j_el['query']['pages']:
            if 'extlinks' in j_el['query']['pages'][page_id]:
                els=adapt_extlinks(j_el['query']['pages'][page_id]['extlinks'])
                data['extlinks']=els

        j_ll=obtain_results_from_api(url, params_langlinks)
        if page_id in j_ll['query']['pages']:
            if 'langlinks' in j_ll['query']['pages'][page_id]:
                lls=filter_langlinks(j_ll['query']['pages'][page_id]['langlinks'], other_languages)
                data['langlinks']=lls
    
        j_wt=obtain_results_from_api(url, params_wikitext)
        if int(page_id)==int(j_wt['parse']['pageid']):
            data['wikitext']=j_wt['parse']['wikitext']
    return data

def get_uri_from_title(name, lang):

    URL = "https://%s.wikipedia.org/w/api.php" % lang

    PARAMS = {
    "action": "query",
    "format": "json",
    "titles": name,
    "prop": "info",
    "inprop": "url|talkid"
    }

    j=obtain_results_from_api(URL, PARAMS)
    for page_id, page_info in j['query']['pages'].items():
        if page_id=='-1': continue
        return page_info['canonicalurl']
    invented_uri="https://%s.wikipedia.org/wiki/%s" % (lang, name.replace(' ', '_'))
    return invented_uri

