from collections import defaultdict
import os
import pickle
from lxml import etree
import inspect


def mapping_wid2tid(doc):
    """
    create mapping from w_id to t_id

    :param lxml.etree._ElementTree doc: XML document loaded by lxml.etree

    :rtype: dict
    :return: w_id -> t_id

    :raises: Exception when a w_id maps to more than one t_id
    :raises: Exception when a t_id maps to more than one w_id
    """
    wid2tid = {}

    for term_el in doc.xpath('terms/term'):
        t_id = term_el.get('id')

        target_els = term_el.findall('span/target')
        assert len(target_els) == 1, f'expecting one target el per term, found {len(target_els)}'

        for target_el in term_el.xpath('span/target'):
            w_id = target_el.get('id')

            if w_id in wid2tid:
                raise Exception(f'{w_id} maps to two or more t_ids')
            else:
                wid2tid[w_id] = t_id

    return wid2tid


def get_entity2occurrences(paths, verbose=0):
    """
    load mapping between entity -> occurrences in text

    :param iterable paths: iterable of NAF files

    :rtype: dict
    :return: entity -> list of occurrences
    """
    entity2occurences = defaultdict(list)

    for path in paths:
        basename = os.path.basename(path)[:-4]
        doc = etree.parse(path)

        t_id2lemma = {term_el.get('id'): term_el.get('lemma')
                      for term_el in doc.xpath('terms/term')}

        for entity_el in doc.xpath('entities/entity'):

            ext_ref_el = entity_el.find('externalReferences/externalRef')
            if ext_ref_el is not None:
                entity = ext_ref_el.get('reference')

                t_ids = [target_el.get('id')
                         for target_el in entity_el.xpath('references/span/target')]

                mention = ' '.join([t_id2lemma[t_id] for t_id in t_ids])
                identifier = basename + '-'.join(t_ids)

                assert t_ids, f'no {t_ids} found'
                entity2occurences[entity].append((basename, identifier, mention))

    if verbose:
        print()
        print(f'function {inspect.stack()[0][3]}')
        print(f'processed {len(paths)} NAF files')
        print(f'found {len(entity2occurences)} different entities')

    return entity2occurences


def load_lang2paths(binfile_paths, naf_folder, verbose=0):
    """

    :param list binfile_paths: path to IncidentCollection objects from classes.py
    :param str naf_folder: folder where NAF files are stored

    :rtype: dict
    :return: lang -> list of paths
    """
    lang2paths = defaultdict(list)

    for binfile_path in binfile_paths:
        with open(binfile_path, 'rb') as infile:
            collection = pickle.load(infile)

        for incident in collection.incidents:
            for ref_text_obj in incident.reference_texts:
                path = os.path.join(naf_folder, f'{ref_text_obj.name}.naf')
                assert os.path.exists(path)
                lang2paths[ref_text_obj.language].append(path)


    if verbose:
        print()
        print(f'function {inspect.stack()[0][3]}')
        for lang, paths in lang2paths.items():
            print(f'{lang}: {len(paths)} files found')

    return lang2paths


def get_entity2frames_and_roles(naf_folder_entities,
                                naf_folder_srl,
                                basename,
                                verbose=0):
    path_entities = f'pilot_data/naf_with_entities/{basename}.naf'
    path_srl = f'pilot_data/naf_srl/NAF/{basename}.naf'

    for path in [path_entities, path_srl]:
        assert os.path.exists(path), f'{path} does not exist'

    doc_with_entities = etree.parse(path_entities)

    t_id_range2reference = {}
    for entity_el in doc_with_entities.xpath('entities/entity'):
        span_el = entity_el.find('references/span')
        t_id_range = get_range_of_targets(span_el)
        reference_el = entity_el.find('externalReferences/externalRef')

        if reference_el is not None:
            reference = reference_el.get('reference')
            t_id_range2reference[t_id_range] = reference

    doc_with_srl = etree.parse(path_srl)

    entity2frames_and_roles = defaultdict(list)

    for predicate_el in doc_with_srl.xpath('srl/predicate'):

        predicate_and_roles = []
        frame = predicate_el.get('uri')

        predicate_range = get_range_of_targets(predicate_el.find('span'))
        predicate_and_roles.append((frame, 'predicate', predicate_range))

        for role_el in predicate_el.xpath('role'):
            role = role_el.get('semRole')
            role_range = get_range_of_targets(role_el.find('span'))
            predicate_and_roles.append((frame, role, role_range))

        for frame, role, srl_range in predicate_and_roles:
            for ent_range, entity in t_id_range2reference.items():
                match = range_overlap(ent_range, srl_range)
                if match:
                    entity2frames_and_roles[entity].append((frame, role))

    return entity2frames_and_roles


def range_overlap(range1, range2):
    """
    determine range1 is within range2 (or is completely the same)

    :param range range1: a range
    :param range range2: another range

    :rtype: bool
    :return: True, range1 is subset of range2, False, not the case
    """
    result = all([
        range1.start >= range2.start,
        range1.stop <= range2.stop
    ])

    return result


assert range_overlap(range(1, 2), range(1, 2))  # identity
assert range_overlap(range(1, 2), range(1, 3))  # subset
assert range_overlap(range(1, 3), range(1, 2)) == False  # superset
assert range_overlap(range(4, 5), range(1, 2)) == False


def get_range_of_targets(span_el):
    targets = []

    children = span_el.xpath('target')
    if children:
        targets = []
        for target_el in children:
            token_id = target_el.get('id')
            number = int(token_id[1:])
            targets.append(number)
        the_range = range(targets[0], targets[-1] + 1)

        for target in targets:
            assert target in the_range, f'{target} not in range {the_range}'
    else:
        the_range = tuple()

    return the_range


example = etree.fromstring("""<span></span>""")
assert get_range_of_targets(example) == tuple()
example = etree.fromstring("""<span><target id="t351"/></span>""")
assert get_range_of_targets(example) == range(351, 352)
example = etree.fromstring("""<span><target id="t351"/><target id="t352"/><target id="t353"/></span>""")
assert get_range_of_targets(example) == range(351, 354)


def get_naf_paths(incidents, event_type, language='en', verbose=0):
    
    naf_paths = []
    for incident, info in incidents.items():
        if info['event_type'] == event_type:
            for ref_text_info in info['reference_texts']['en']:
                naf = ref_text_info['naf_basename']
                path = f'{pilot_folder}/naf_srl/NAF/{naf}'
                assert os.path.exists(path), f'{path} does not exist'
                naf_paths.append(path)
    
    if verbose >= 1:
        print()
        print(f'found {len(naf_paths)} NAF paths for {event_type} and {language}')
    return naf_paths
                

def get_label2freq(naf_paths, xpath_query, attributes, verbose=0):
    label2freq = defaultdict(int)
    for naf_path in naf_paths:
        doc = etree.parse(naf_path)
        for el in doc.xpath(xpath_query):
            values = [el.get(attribute)
                      for attribute in attributes]
            value_string = '---'.join(values)
            label2freq[value_string] += 1
            
    if verbose >= 1:
        print()
        print(f'ran function with {xpath_query} {attributes}')
        print(f'found {sum(label2freq.values())} occurrences of {len(label2freq)} unique labels')
    
    return label2freq


def load_start_and_end_offset_to_tid(naf):
    """
    """
    wid2tid = {}
    for term_el in naf.xpath('terms/term'):
        tid = term_el.get('id')
        for span_el in term_el.xpath('span/target'):
            wid = span_el.get('id')
            wid2tid[wid] = tid

    start2tid = {}
    end2tid = {}

    for wf_el in naf.xpath('text/wf'):
        wid = wf_el.get('id')
        start_offset = int(wf_el.get('offset'))
        end_offset = start_offset + int(wf_el.get('length'))

        start2tid[start_offset] = wid2tid[wid]
        end2tid[end_offset] = wid2tid[wid]

    return start2tid, end2tid


def get_range_of_tids(start_tid, end_tid):
    start = int(start_tid[1:])
    end = int(end_tid[1:])
    the_range = range(start, end + 1)

    assert end >= start, f'{end_tid} should not be higher than {start_tid}'

    return [f't{number}'
            for number in the_range]


assert get_range_of_tids('t10', 't10') == ['t10']
assert get_range_of_tids('t10', 't11') == ['t10', 't11']
assert get_range_of_tids('t10', 't12') == ['t10', 't11', 't12']
# assert get_range_of_tids('t12', 't10') # should raise exception