import bz2
import json
import os
import urllib.parse

from lxml import etree
import xml_utils


def load_annotations(annotations, prefix):
    """
    load list of dicts in the form of
    {'surface_form': 'Mannheim', 'uri': 'Mannheim', 'offset': 52}

    to

    :rtype: dict
    :return: (start_offset, end_offset) -> (surface_form, uri)
    """
    start_end2info = {}

    for annotation in annotations:
        start = annotation['offset']
        sf = annotation['surface_form']
        uri = f'{prefix}{annotation["uri"]}'
        uri = urllib.parse.unquote(uri)

        end = start + len(sf)

        start_end2info[(start, end)] = (sf, uri)

    return start_end2info


def urlencode_wikititle(wiki_title, prefix=None):
    """
    We perform two steps:
    1. replace spaces with underscores
    2. urllib.parse.quote_plus() on string

    :param str wiki_title: title of Wikipedia page, .e.g, François Hollande
    """
    with_underscores = wiki_title.replace(' ', '_')
    url_encoded = urllib.parse.quote_plus(with_underscores)

    if prefix is not None:
        result = f'{prefix}{url_encoded}'
    else:
        result = url_encoded

    return result

result = urlencode_wikititle('François Hollande', prefix='https://nl.wikipedia.org/wiki/')
assert result == 'https://nl.wikipedia.org/wiki/Fran%C3%A7ois_Hollande'

def load_wiki_page_info(wiki_title,
                        prefix,
                        language,
                        wiki_folder,
                        wiki_uri2relative_path):
    """
    :param str wiki_title: Wikipedia article title, e.g., "President van Frankrijk"
    :param str language: supported: 'nl' | 'en' | 'it'
    :param str wiki_folder: path to where extracted Wikipedia output is stored, e.g, the folder "wiki",
    with subfolders for the output per language

    :rtype: tuple
    :return: (success, reason, naf)
    """

    success = True
    reason = 'success'
    naf = None

    assert language in {'nl', 'en', 'it'}, f'{language} not part of supported languages: nl it en'

    # try to retrieve JSON of Wikipedia article
    wiki_uri = f'{prefix}{wiki_title.replace(" ", "_")}'
    wiki_uri_encoded = urlencode_wikititle(wiki_title, prefix=prefix)

    if wiki_uri_encoded not in wiki_uri2relative_path:
        reason = 'page not extracted'
        success = False
        return None, None, success, reason
    else:
        relative_path, line_number = wiki_uri2relative_path[wiki_uri_encoded]
        path = os.path.join(wiki_folder, relative_path)

        # load wiki_page
        wiki_page = {}
        with bz2.BZ2File(path, "r") as infile:
            for index, line in enumerate(infile):
                if index == line_number:
                    wiki_page = json.loads(line)
                    break

        assert wiki_page, f'index is wrong for {language} {wiki_title}'

        return wiki_page['text'], wiki_page['annotations'], success, reason

if __name__ == '__main__':
    import spacy
    import os
    import shutil
    import json
    import pickle
    from datetime import datetime
    from collections import Counter
    print('start', datetime.now())

    spacy_models = "en-en_core_web_sm;nl-nl_core_news_sm;it-it_core_news_sm"
    wiki_folder = '/home/postma/Wikipedia_Reader/wiki'
    naf_output_folder = 'wiki_output'

    if os.path.exists(naf_output_folder):
        shutil.rmtree(naf_output_folder)

    verbose = 1
    language2extraction_succes = {
        'nl' : [],
        'en' : [],
        'it' : []
        }

    # load spaCy models
    models = {}
    for model_info in spacy_models.split(';'):
        language, model_name = model_info.split('-')
        models[language] = spacy.load(model_name)

    # load index and language info
    path_uri2path_info = os.path.join(wiki_folder, 'page2path.p')
    with open(path_uri2path_info, 'rb') as infile:
        wiki_uri2path_info = pickle.load(infile) # make take some time

    language_info_path = os.path.join(wiki_folder, 'language2info.json')
    with open(language_info_path, 'r')  as infile:
        language2info = json.load(infile)

    # load bin file
    bin_path = 'bin/election_nl,it,ja,en,pilot.bin'
    with open(bin_path, 'rb') as infile:
        incident_coll = pickle.load(infile)

    count = 0
    for incident_obj in incident_coll.incidents:

        count += 1
        if count == 100:
            break 

        for ref_text_obj in incident_obj.reference_texts:
            wiki_title = ref_text_obj.name
            language = ref_text_obj.language
            prefix = language2info[language]['prefix']
            year, month, day = language2info[language]['year_month_day']
            dct = datetime(year, month, day)
            nlp = models[language]

            succes, reason, naf = run_spacy_on_wiki_text_and_add_hyperlinks(wiki_title,
                                                          prefix,
                                                          language,
                                                          nlp,
                                                          wiki_folder,
                                                          wiki_uri2path_info,
                                                          dct,
                                                          output_folder=naf_output_folder,
                                                          verbose=verbose)
            language2extraction_succes[language].append(succes)

    for language, info in language2extraction_succes.items():
        print(language, Counter(info))

    print('end', datetime.now())
