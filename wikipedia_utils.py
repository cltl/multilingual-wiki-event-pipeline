import bz2
import json
import os
import urllib.parse

from lxml import etree
import spacy_to_naf
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



def add_hyperlinks(naf, annotations, prefix, verbose=0):
    """

    :param lxml.etree._Element naf: the root element of the XML file    :param wiki_page:
    :param list annotations: list of annotations, e.g.,
    {"surface_form": "buco nero binario", "uri": "Buco_nero_binario", "offset": 20288}
    :param str prefix: the wikipedia prefix of the language, e.g.,
    https://nl.wikipedia.org/wiki/
    :param verbose:
    :return:
    """
    from_start2tid, from_end2tid = xml_utils.load_start_and_end_offset_to_tid(naf)
    start_end2info = load_annotations(annotations,
                                      prefix=prefix)

    start_offset2token = {int(w_el.get('offset')) : w_el.text
                          for w_el in naf.xpath('text/wf')}

    next_id = 1
    entities_layer = etree.SubElement(naf, "entities")
    for (start, end), (sf, uri) in start_end2info.items():

        if start not in from_start2tid:
            if verbose >= 3:
                print(f'MISALIGNMENT {start} not mapped to tid')
            continue
        if end not in from_end2tid:
            if verbose >= 3:
                print(f'MISALIGNMENT {end} not mapped to tid')
            continue

        assert sf.startswith(start_offset2token[start])

        start_tid = from_start2tid[start]
        end_tid = from_end2tid[end]
        t_ids = xml_utils.get_range_of_tids(start_tid,
                                            end_tid)

        entity_data=spacy_to_naf.EntityElement(
                                             eid='e%d' % next_id,
                                             entity_type='UNK',
                                             text=sf,
                                             targets=t_ids,
                                             ext_refs=[{'reference': uri}])
        next_id += 1

        spacy_to_naf.add_entity_element(entities_layer, entity_data, add_comments=True)


def run_spacy_on_wiki_text_and_add_hyperlinks(wiki_title,
                                              prefix,
                                              language,
                                              nlp,
                                              wiki_folder,
                                              wiki_uri2relative_path,
                                              dct,
                                              output_folder=None,
                                              verbose=0):
    """

    :param str wiki_title: Wikipedia article title, e.g., "President van Frankrijk"
    :param str language: supported: 'nl' | 'en' | 'it'
    :param nlp: loaded spaCy model, i.e., results of calling spacy.load('MODELNAME')
    :param str wiki_folder: path to where extracted Wikipedia output is stored, e.g, the folder "wiki",
    with subfolders for the output per language
    :param datetime.datetime dct: document creation time, date of crawling for Wikipedia
    :param output_folder: if provided, the NAF file will be written to
    output_folder/LANGUAGE/WIKI_TITLE.naf

    :rtype: tuple
    :return: (succes, reason, naf)
    """
    succes = True
    reason = 'succes'
    naf = None

    assert language in {'nl', 'en', 'it'}, f'{language} not part of supported languages: nl it en'

    # try to retrieve JSON of Wikipedia article
    wiki_uri = f'{prefix}{wiki_title.replace(" ", "_")}'
    wiki_uri_encoded = urlencode_wikititle(wiki_title, prefix=prefix)

    if verbose >= 2:
        print(wiki_uri) 

    if wiki_uri_encoded not in wiki_uri2relative_path:
        reason = 'page not extracted'
        succes = False
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

        # parse with spaCy
        naf = spacy_to_naf.text_to_NAF(text=wiki_page['text'],
                                       nlp=nlp,
                                       dct=dct,
                                       layers={'raw', 'text', 'terms'},
                                       title=wiki_title,
                                       uri=wiki_uri,
                                       language=language)


        assert naf.find('raw').text == wiki_page['text'], f'mismatch between raw text JSON and NAF file'

        # add hyperlinks as entity elements
        add_hyperlinks(naf,
                       wiki_page['annotations'],
                       prefix,
                       verbose=verbose)

        # if wanted, write output to disk
        if output_folder is not None:
            if not os.path.exists(output_folder):
                os.mkdir(output_folder)
            lang_dir = os.path.join(output_folder, language)
            if not os.path.exists(lang_dir):
                os.mkdir(lang_dir)

            output_path = os.path.join(lang_dir, f'{wiki_title}.naf')
            with open(output_path, 'w') as outfile:
                naf_string = spacy_to_naf.NAF_to_string(naf)
                outfile.write(naf_string)
            if verbose >= 2:
                print(f'written {wiki_title} ({language}) to {output_path}')


    message = f'succes:{succes} with reason: {reason} for {wiki_title} ({language})'
    if verbose >= 3:
        print(message)

    if all([verbose == 2,
            not succes]):
        print(message)

    # return message whether it was succesful
    return succes, reason, naf




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
