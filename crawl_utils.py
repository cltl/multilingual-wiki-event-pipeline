from collections import Counter
import urllib
import http
import ast
import socket
from urllib.parse import urlencode
import urllib3

import classes

from newsplease import NewsPlease

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
    status = 'succes'
    wb_url = None

    params = {'url': url,
              'output' : format,
              'limit' : last_n}

    encoded_uri = WAYBACK_CDX_SERVER + urlencode(params)
    r = http.request('GET', encoded_uri)

    if verbose >= 3:
        print(encoded_uri)

    if r.status != 200:
        status = 'status code not 200'
        if verbose >= 3:
            print(f'status code: {r.status_code}')

    if status == 'succes':
        data_as_string = r.data.decode('utf-8')
        snapshots = ast.literal_eval(data_as_string[:-1])

        for (urlkey,
             timestamp,
             original,
             mimetype,
             statuscode,
             digest,
             length) in snapshots[1:]:
            if int(statuscode) == 200:
                wb_url = f'http://web.archive.org/web/{timestamp}/{original}'

    return status, wb_url


def run_newsplease(url,
                   timeout,
                   startswith=None,
                   accepted_languages=set(),
                   excluded_domains=set(),
                   title_required=True,
                   num_chars_range=False,
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

    :rtype: tuple
    :return (status, None of dict with all NewsPlease information)
    """
    status = 'succes'
    news_please_info = None

    if startswith:
        if not url.startswith(startswith):
            status = 'not a valid url'

    if 'web.archive.org/web/' not in url:
        wb_status, wb_url = generate_wayback_uri(url, verbose=0)
    else:
        wb_status = 'succes'
        wb_url = url

    if wb_status != 'succes':
        status = 'No Waybach Machine URL found'

    # TODO: what if url is not the same as the one crawler (via redirects?)

    if status == 'succes':
        try:
            article = NewsPlease.from_url(wb_url, timeout=timeout)

            if article is None:
                status = 'crawl error'
            elif article.text is None:
                status = 'crawl error'

        except (urllib.error.URLError,
                ValueError,
                http.client.RemoteDisconnected,
                socket.timeout) as e:
            article = None
            status = 'URL error'

    if status == 'succes':

        # validate attributes based on settings
        news_please_info = article.get_dict()

        if news_please_info['source_domain'] in excluded_domains:
            status = 'excluded domain'

        if accepted_languages:
            if news_please_info['language'] not in accepted_languages:
                status = 'not in accepted languages'

        if num_chars_range:
            num_chars = len(news_please_info['text'])
            if num_chars not in num_chars_range:
                status = 'outside of accepted number of characters range'

        if title_required:
            if news_please_info['title'] is None:
                status = 'no title'

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
            print(status, url)

    return status, news_please_info

status, article = run_newsplease(url='https://www.aasdfjsoidfj.nl',
                                 timeout=10)
assert status == 'URL error'

status, article = run_newsplease(url='https://www.rt.com/news/203203-ukraine-russia-troops-border/',
                                 timeout=10)
assert status == 'succes'

def get_ref_text_obj_of_primary_reference_texts(urls,
                                                timeout,
                                                startswith=None,
                                                accepted_languages=set(),
                                                excluded_domains=set(),
                                                title_required=True,
                                                num_chars_range=False,
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
    # TODO: descriptive statistics about succes rate regarding various properties
    # TODO: file paths for those files
    url_to_info = {}

    for url in urls:
        status, result = run_newsplease(url,
                                        timeout=timeout,
                                        startswith=startswith,
                                        excluded_domains=excluded_domains,
                                        accepted_languages=accepted_languages,
                                        title_required=title_required,
                                        num_chars_range=num_chars_range,
                                        verbose=verbose)

        info = {
            'status' : None,
            'web_archive_uri' : None,
            'name' : None,
            'creation_date' : None,
            'language' : None,
            'found_by' : None,
            'content' : None,
        }

        if status == 'succes':
            info['status'] = status
            info['web_archive_uri']  = result['url']
            info['name'] = result['title']
            info['creation_date'] = result['date_publish']
            info['language'] = result['language']
            info['found_by'] = 'Wikipedia source'
            info['content'] = result['text']
        url_to_info[url] = info


    url_to_ref_text_obj = {}
    for url, info in url_to_info.items():
        if info['status'] == 'succes':
            ref_text_obj = classes.ReferenceText(
                uri=url,
                web_archive_uri=info['web_archive_uri'],
                name=info['name'],
                content=info['content'],
                language=info['language'],
                creation_date=info['creation_date'],
                found_by=[info['found_by']]
            )

            url_to_ref_text_obj[url] = ref_text_obj

    if verbose >= 2:
        print()
        print(f'processed {len(urls)} urls')
        print(f'represented {len(url_to_ref_text_obj)} as ReferenceText object')

    return url_to_ref_text_obj


if __name__ == '__main__':

    urls = ['http://www.tvweeklogieawards.com.au/logie-history/2000s/2005/',
            'http://www.australiantelevision.net/awards/logie2005.html',
            'https://www.smh.com.au/entertainment/once-twice-three-times-a-gold-logie-20050502-gdl8io.html',
            'https://www.imdb.com/event/ev0000401/2005/',
            'https://web.archive.org/web/20140126184012/http://www.tvweeklogieawards.com.au/logie-history/2000s/2005/']

    exluded_domains = {'www.jstor.org'}
    accepted_languages = {'en'}
    title_required = True
    num_chars_range = range(100, 10001)
    startswith = 'http'
    timeout = 2

    url_to_info = get_ref_text_obj_of_primary_reference_texts(urls,
                                                              timeout,
                                                              startswith=startswith,
                                                              accepted_languages=accepted_languages,
                                                              excluded_domains=exluded_domains,
                                                              title_required=True,
                                                              num_chars_range=num_chars_range,
                                                              verbose=2)