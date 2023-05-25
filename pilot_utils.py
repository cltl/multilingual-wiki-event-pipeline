import json
import os
import re
import time
import urllib.parse
from datetime import datetime
#Pia: adding named tuple for entity elements
from collections import namedtuple

import spacy_to_naf
from spacy_to_naf.converter import Converter

from lxml import etree

import native_api_utils as api
import utils
import xml_utils

eventtype2json = {}
for_encoding = 'é'


# , 'tennis tournament': 'tennis tournament'}

# Pia: added entity tuple  object here
EntityElement = namedtuple('EntityElement', ['eid',
                                     'entity_type',
                                     'targets',
                                     'text',
                                     'ext_refs' # list of dictionaries, e.g., [{'reference' : 'Naples',
                                                                              # 'resource' : 'Wikipedia'}]
                                     ])

def add_entity_element(entities_layer,
                       naf_version,
                       entity_data,
                       add_comments=False):
    """
    Function that adds an entity element to the entity layer.
    """
    entity_el = etree.SubElement(entities_layer, "entity")
    entity_el.set("id", entity_data.eid)
    entity_el.set("type", entity_data.entity_type)

    if naf_version == 'v3':
        references_el = etree.SubElement(entity_el, "references")
        span = etree.SubElement(references_el, "span")
    elif naf_version == 'v3.1':
        span = etree.SubElement(entity_el, "span")

    if add_comments:
        text = ' '.join(entity_data.text)
        text = prepare_comment_text(text)
        span.append(etree.Comment(text))
    for target in entity_data.targets:
        target_el = etree.SubElement(span, "target")
        target_el.set("id", target)

    assert type(entity_data.ext_refs) == list, f'ext_refs should be a list of dictionaries (can be empty)'
    ext_refs_el = etree.SubElement(entity_el, 'externalReferences')
    for ext_ref_info in entity_data.ext_refs:
        one_ext_ref_el = etree.SubElement(ext_refs_el, 'externalRef')
        one_ext_ref_el.set('reference', ext_ref_info['reference'])

        for optional_attr in ['resource', 'source', 'timestamp']:
            if optional_attr in ext_ref_info:
                one_ext_ref_el.set(optional_attr, ext_ref_info[optional_attr])


def prepare_comment_text(text):
    "Function to prepare text to be put inside a comment."
    text = text.replace('--','DOUBLEDASH')
    if text.endswith('-'):
        text = text[:-1] + 'SINGLEDASH'
    return text

def remove_incidents_with_missing_FEs(incidents, event_type):
    new_incidents = []

    print('EType', event_type, eventtype2json.keys())
    if event_type in eventtype2json.keys():
        jsonfilename = 'wdt_fn_mappings/%s.json' % eventtype2json[event_type]
    else:
        jsonfilename = 'wdt_fn_mappings/any.json'

    with open(jsonfilename, 'rb') as f:
        wdt_fn_mappings_COL = json.load(f)

    all_frame_elements = set(wdt_fn_mappings_COL.keys())

    for incident in incidents:
        extra_info_keys = set(incident.extra_info.keys())
        if extra_info_keys == all_frame_elements:
            new_incidents.append(incident)
    return new_incidents


def check_ref_text(rt, min_chars=100, max_chars=10000):
    num_chars = len(rt.content)
    if num_chars < min_chars or num_chars > max_chars:
        return False
    if re.match(r'.*[1-2]([0-9]){3}-[1-2]([0-9]){3}.*$', rt.name):
        return False
    return True


def skip_this_incident(ref_texts,
                       target_languages,
                       rt_langs,
                       must_have_all_languages=True,
                       must_have_english=True,
                       one_page_per_language=True):
    """ Perform language checks depending on flags set in the config file."""
    skip_incident = False
    if must_have_all_languages:
        for target_lang in target_languages:
            if target_lang not in rt_langs:
                skip_incident = True
                break
    if must_have_english and 'en' not in rt_langs:
        skip_incident = True
    elif one_page_per_language and len(ref_texts) != len(rt_langs):
        skip_incident = True
    return skip_incident


def create_pilot_data(data,
                      target_languages,
                      must_have_all_languages,
                      must_have_english,
                      one_page_per_language):
    pilot_incidents = set()

    cached = {}

    data.incidents = remove_incidents_with_missing_FEs(data.incidents, data.incident_type)
    for incident in data.incidents:
        langs = set()
        incident.reference_texts = utils.deduplicate_ref_texts(incident.reference_texts)
        new_ref_texts = []
        for ref_text in incident.reference_texts:
            ref_text.content = ref_text.content.split('==')[0].strip()  # first section
            if check_ref_text(ref_text, max_chars=50000):
                langs.add(ref_text.language)
                new_ref_texts.append(ref_text)
        incident.reference_texts = new_ref_texts

        if skip_this_incident(new_ref_texts,
                              target_languages,
                              langs,
                              must_have_all_languages,
                              must_have_english,
                              one_page_per_language):
            continue

        for ref_text in incident.reference_texts:
            if not ref_text.uri:
                ref_text.uri = api.get_uri_from_title(ref_text.name, ref_text.language)
        pilot_incidents.add(incident)
        for p, v_set in incident.extra_info.items():
            new_v_set = set()
            for v in v_set:
                if '|' not in v:
                    label = ''
                    q_id = v.split('/')[-1]
                    if q_id in cached.keys():
                        label = cached[q_id]
                    elif v.startswith('http'):
                        label = utils.obtain_label(q_id)
                        time.sleep(1)
                        cached[q_id] = label
                    v += ' | ' + label
                    new_v_set.add(v)
                else:
                    new_v_set.add(v)
            incident.extra_info[p] = new_v_set
    print('Num of pilot incidents', len(pilot_incidents))
    return pilot_incidents


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


def time_in_correct_format(datetime_obj):
    "Function that returns the current time"
    return datetime_obj.strftime("%Y-%m-%dT%H:%M:%SUTC")



def add_hyperlinks(naf, annotations, prefix, language, dct, wiki_langlinks={}, verbose=0):
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

    start_offset2token = {int(w_el.get('offset')): w_el.text
                          for w_el in naf.xpath('text/wf')}

    next_id = 1
    naf = naf.getroot()
    entities_layer = etree.SubElement(naf, "entities")

    naf_header = naf.find('nafHeader')
    ling_proc = etree.SubElement(naf_header, "linguisticProcessors")
    ling_proc.set("layer", 'entities')
    lp = etree.SubElement(ling_proc, "lp")
    the_time = time_in_correct_format(dct)
    lp.set("beginTimestamp", the_time)
    lp.set('endTimestamp', the_time)
    lp.set('name', 'Wikipedia hyperlinks')
    lp.set('version', 'Wikipedia dump from 2019-07-20')  # TODO: change this if we move to other version of Wikipedia

    date = datetime(2019, 7, 20)
    date_as_string = time_in_correct_format(date)


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

        ext_refs = [{'resource': 'Wikipedia hyperlinks',
                     'reference': uri,
                     'source': 'https://www.wikipedia.org/',
                     'timestamp' : date_as_string}]
        if wiki_langlinks:
            for lang, uri in wiki_langlinks[language][uri].items():
                ext_refs.append({'resource': 'Wikipedia hyperlinks',
                                 'reference': uri,
                                 'source' : 'https://www.wikipedia.org/',
                                 'timestamp' : date_as_string})

        entity_data = EntityElement(
            eid='e%d' % next_id,
            entity_type='UNK',
            text=sf,
            targets=t_ids,
            ext_refs=ext_refs)



        next_id += 1

        add_entity_element(entities_layer,
                                        'v3.1',
                                        entity_data,
                                        add_comments=True)


def text_to_naf(wiki_title,
                target_languages,
                text,
                wiki_uri,
                annotations,
                prefix,
                language,
                nlp,
                dct,
                output_folder=None,
                wiki_langlinks={},
                verbose=0):
    assert language in target_languages, f'{language} not part of supported languages: {" ".join(target_languages)}'

    # prepare output path
    if output_folder is not None:
        print("Creating naf folder")
        if not os.path.exists(output_folder):
            os.mkdir(output_folder)
        lang_dir = os.path.join(output_folder, language)
        if not os.path.exists(lang_dir):
            os.mkdir(lang_dir)
        output_path = os.path.join(lang_dir, f'{wiki_title}.naf')
    else:
        output_path = 'dummpy.naf'


    # parse with spaCy
    add_mw = False
    if language in {'en', 'nl'}:
        add_mw = True
    if language == 'en':
        converter = Converter('en_core_web_sm', add_terms=True, add_deps=True, add_entities=False, add_chunks=False)
    elif language == 'nl':
        converter = Converter('nl_core_news_sm', add_terms=True, add_deps=True, add_entities=False, add_chunks=False)

    try:
        # naf = spacy_to_naf.text_to_NAF(text=text,
        #                                nlp=nlp,
        #                                dct=dct,
        #                                layers={'raw', 'text', 'terms', 'deps'},
        #                                naf_version='v3.1',
        #                                title=wiki_title,
        #                                uri=wiki_uri,
        #                                language=language,
        #                                add_mws=add_mw)
        naf = converter.process_text(text, output_path)
        #naf = naf.root
        naf = naf.tree
        # print('naf after tree')
        # print(type(naf))
        # print(help(naf.write))
        assert naf.find('raw').text == text, f'mismatch between raw text JSON and NAF file'

    except:
        print("Did not write to files- problem:")
        return
        # naf = converter.process_text(text, output_path)



    # add hyperlinks as entity elements
    add_hyperlinks(naf,
                   annotations,
                   prefix,
                   language,
                   dct,
                   wiki_langlinks=wiki_langlinks)

    # if wanted, write output to disk
    if output_folder is not None:
        # print("Creating naf folder")
        # if not os.path.exists(output_folder):
        #     os.mkdir(output_folder)
        # lang_dir = os.path.join(output_folder, language)
        # if not os.path.exists(lang_dir):
        #     os.mkdir(lang_dir)
        # output_path = os.path.join(lang_dir, f'{wiki_title}.naf')
        print("Storing naf file:", output_path)

        #spacy_to_naf.NAF_to_file(naf, output_path)
        # naf.write(output_path)
        # print(type(naf))
        # print(dir(naf))
        # tree = etree.ElementTree(naf)
        naf.write(output_path, pretty_print=True)

    if verbose >= 3:
        print(f'saved to {output_path}')

    return naf
