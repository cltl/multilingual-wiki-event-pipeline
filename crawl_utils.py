from collections import defaultdict
import urllib
import http
import ast
import socket
from urllib.parse import urlencode
import urllib3

import classes

from newsplease import NewsPlease
import langdetect
import lxml

for_encoding = 'é'
WAYBACK_CDX_SERVER = 'http://web.archive.org/cdx/search/cdx?'

def generate_wayback_uri(url,
                         last_n=-5,
                         format='json',
                         verbose=0):
    """
    call the https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server#basic-usage
    API to obtain the last snapshots of the wayback machine for a specific URL.

    :param str url: a URL
    :param int last_n: -5 indicates the 5 latest snapshots and 5 the first 5 snapshots
    :param str format: supported: 'json'

    :rtype: tuple
    :return: (status, URL or None)
    """
    http = urllib3.PoolManager()
    wb_url = None

    params = {'url': url,
              'output' : format,
              'limit' : last_n}

    encoded_uri = WAYBACK_CDX_SERVER + urlencode(params)
    print(encoded_uri)

    try:
        r = http.request('GET', encoded_uri)
    except urllib3.exceptions.MaxRetryError:
        return 'http request failed', url

    if r.status != 200:
        status = 'status code not 200'
        if verbose >= 4:
            print(f'status code: {r.status}')

    data_as_string = r.data.decode('utf-8')

    try:
        snapshots = ast.literal_eval(data_as_string[:-1])
    except:
        # org.archive.util.io.RuntimeIOException: org.archive.wayback.exception.AdministrativeAccessControlException: Blocked Site Error
        snapshots = ['']

    for (urlkey,
         timestamp,
         original,
         mimetype,
         statuscode,
         digest,
         length) in snapshots[1:]:

        if statuscode == '-':
            continue

        if int(statuscode) == 200:
            wb_url = f'http://web.archive.org/web/{timestamp}/{original}'
            status = 'succes'

    if wb_url is None:
        status = 'Wayback Machine URL not found'

    if status == 'succes':
        if verbose >= 3:
            print()
            print(f'Wayback machine: {wb_url} for url {url}')
            print(f'used the following query: {encoded_uri}')

    return status, wb_url


def run_newsplease(url,
                   timeout,
                   startswith=None,
                   accepted_languages=set(),
                   excluded_domains=set(),
                   title_required=True,
                   num_chars_range=False,
                   illegal_substrings=[],
                   illegal_chars_in_title=set(),
                   verbose=0):
    """
    apply newsplease on a url

    :param str url: a url to crawl
    :param int timeout: timeout in seconds
    :param startswith: if provided, the url has to start with this prefix, e.g., http
    :param set accepted_languages: set of languages that are accepted
    (https://en.wikipedia.org/wiki/ISO_639-1)
    :param bool title_required: the article.title value can not be None
    :param num_chars_range: if of type range, an article will only be included
    if the number of characters falls within the specified range.
    :param set illegal_substrings: if an article contains any of these substrings,
    do not include them

    :rtype: tuple
    :return (status, None of dict with all NewsPlease information)
    """
    status = 'succes'
    wb_url = None
    news_please_info = None

    if startswith:
        if not url.startswith(startswith):
            status = 'not a valid url'

    for excluded_domain in excluded_domains:
        if excluded_domain in url:
            status = 'excluded domain'
    if status == 'succes':
        if 'web.archive.org/web/' not in url:
            print('generating wayback uri')
            status, wb_url = generate_wayback_uri(url, verbose=verbose)
            print(status, wb_url)
        else:
            status = 'succes'
            wb_url = url

    # TODO: what if url is not the same as the one crawler (via redirects?)

    if status == 'succes':
        print('trying to crawl')
        try:
            print(wb_url)
            article = NewsPlease.from_url(wb_url, timeout=timeout)
            #article.download()
            #print(article.title)
            # article = NewsPlease.from_url('https://www.nytimes.com/2017/02/23/us/politics/cpac-stephen-bannon-reince-priebus.html?hp')
            # print(article.title)

            if article is None:
                status = 'crawl error'
            elif article.title is None:
                status = 'crawl error'

        except (urllib.error.URLError,
                ValueError,
                http.client.RemoteDisconnected,
                socket.timeout,
                http.client.IncompleteRead,
                http.client.RemoteDisconnected,
                ConnectionResetError,
                lxml.etree.ParserError,
                langdetect.lang_detect_exception.LangDetectException
                ) as e:
            article = None
            status = 'URL error'

    if status == 'succes':

        # validate attributes based on settings
        news_please_info = article.get_dict()

        if accepted_languages:
            if news_please_info['language'] not in accepted_languages:
                status = 'not in accepted languages'

        for illegal_substring in illegal_substrings:
            if illegal_substring in news_please_info['maintext']:
                status = 'illegal substring'

        if num_chars_range:
            num_chars = len(news_please_info['maintext'])
            if num_chars not in num_chars_range:
                status = 'outside of accepted number of characters range'

        if title_required:
            if news_please_info['title'] is None:
                status = 'no title'
            else:
                for illegal_char_in_title in illegal_chars_in_title:
                    if illegal_char_in_title in news_please_info['title']:
                        status = 'illegal char in title'

    if verbose >= 3:
        if status == 'succes':
            print()
            print(f'{status} {url}')
            if status == 'succes':
                attrs = ['title',
                         'url',
                         'date_publish',
                         'source_domain',
                         'language']

            for attr in attrs:
                print(f'ATTR {attr}: {getattr(article, attr)}')

            print('num chars', len(news_please_info['text']))
        else:
            print()
            print(status, wb_url, url)

    return status, news_please_info

status, article = run_newsplease(url='https://www.aasdfjsoidfj.nl',
                                 timeout=10)
print('test 1 - should fail with wayback machine url not found')
print(status)
assert status == 'Wayback Machine URL not found'

# Pia: link seems to have disappeared - creating new test
# status, article = run_newsplease(url='https://www.rt.com/news/203203-ukraine-russia-troops-border/',
#                                  timeout=10)
#https://nos.nl/artikel/2312406-rechtbank-verplicht-verdachte-van-tramaanslag-om-naar-zitting-te-komen.html'
#https://www.reuters.com/world/europe/uk-says-russian-forces-opened-new-route-advance-towards-kyiv-2022-02-25/'
status, article = run_newsplease(url='https://nos.nl/artikel/2312406-rechtbank-verplicht-verdachte-van-tramaanslag-om-naar-zitting-te-komen.html',
                                 timeout=10)


print('test 2 - should be successful')
print(status)
assert status == 'succes'



def get_ref_text_obj_of_primary_reference_texts(urls,
                                                timeout,
                                                startswith=None,
                                                accepted_languages=set(),
                                                excluded_domains=set(),
                                                title_required=True,
                                                num_chars_range=False,
                                                illegal_substrings=[],
                                                illegal_chars_in_title=set(),
                                                verbose=0):
    """
    crawl urls using newsplease and represent succesful crawls
    using the classes.ReferenceText object

    :param urls:
    :param timeout: see function "run_newsplease"
    :param startswith: see function "run_newsplease"
    :param accepted_languages: see function "run_newsplease"
    :param excluded_domains: see function "run_newsplease"
    :param title_required: see function "run_newsplease"
    :param num_chars_range: see function "run_newsplease"

    :rtype: dict
    :return: mapping from uri ->
    classes.ReferenceText object
    """
    url_to_info = {}
    stati = defaultdict(int)

    for index, url in enumerate(urls, 1):

        if verbose >= 5:
            if index == 50:
                print(f'QUITTING AFTER 5 BECAUSE VERBOSE == 50')
                break

        status, result = run_newsplease(url,
                                        timeout=timeout,
                                        startswith=startswith,
                                        excluded_domains=excluded_domains,
                                        accepted_languages=accepted_languages,
                                        title_required=title_required,
                                        num_chars_range=num_chars_range,
                                        illegal_substrings=illegal_substrings,
                                        illegal_chars_in_title=illegal_chars_in_title,
                                        verbose=verbose)

        info = {
            'status' : status,
            'web_archive_uri' : None,
            'name' : None,
            'creation_date' : None,
            'language' : None,
            'found_by' : None,
            'content' : None,
        }

        if status == 'succes':
            # Pia: stick title to text
            text = result['text']
            title = result['title']
            text_title = f'{title}\n{text}'
            info['web_archive_uri']  = result['url']
            info['name'] = result['title']
            info['creation_date'] = result['date_publish']
            info['language'] = result['language']
            info['found_by'] = 'Wikipedia source'
            #info['content'] = result['text']
            info['content'] = text_title
        url_to_info[url] = info


    url_to_ref_text_obj = {}
    for url, info in url_to_info.items():
        stati[info['status']] += 1
        if info['status'] == 'succes':
            ref_text_obj = classes.ReferenceText(
                uri=url,
                web_archive_uri=info['web_archive_uri'],
                name=info['name'],
                content=info['content'],
                language=info['language'],
                creation_date=info['creation_date'],
                found_by=[info['found_by']],
            )

            url_to_ref_text_obj[url] = ref_text_obj

    if verbose >= 2:
        print()
        print(f'processed {len(urls)} urls')
        print(f'represented {len(url_to_ref_text_obj)} as ReferenceText object')
        print(stati)


    return url_to_ref_text_obj


if __name__ == '__main__':
    import native_api_utils


    #links = native_api_utils.obtain_primary_rt_links('Aanslag_in_Utrecht_op_18_maart_2019', 'nl')
    links = ['https://nos.nl/artikel/2312406-rechtbank-verplicht-verdachte-van-tramaanslag-om-naar-zitting-te-komen.html']

    exluded_domains = {'jstor.org'}
    accepted_languages = {'nl'}
    title_required = True
    num_chars_range = range(100, 10001)
    startswith = 'http'
    timeout = 4
    illegal_substrings = ["These crawls are part of an effort to archive pages",
                          "Formed in 2009, the Archive Team"]
    illegal_chars_in_title = {'/'}

    url_to_info = get_ref_text_obj_of_primary_reference_texts(urls=links,
                                                              timeout=timeout,
                                                              startswith=startswith,
                                                              accepted_languages=accepted_languages,
                                                              excluded_domains=exluded_domains,
                                                              title_required=True,
                                                              num_chars_range=num_chars_range,
                                                              illegal_substrings=illegal_substrings,
                                                              illegal_chars_in_title=illegal_chars_in_title,
                                                              verbose=2)

    for url, info in url_to_info.items():
        print()
        print(url)
        print(info.web_archive_uri)
        print(info.creation_date)
        print(info.content)
