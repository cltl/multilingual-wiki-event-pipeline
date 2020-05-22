from collections import defaultdict
import os
import pickle
from lxml import etree
import inspect

import utils
import native_api_utils

for_encoding = 'é'
COREFERENCES_ID = 'Wikipedia_hyperlinks'
WIKIDATA_PREFIX = 'http://www.wikidata.org/entity/'

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


def iterable_of_lexical_items(doc,
                              xml_path,
                              selected_attributes,
                              attr_requirements={},
                              verbose=0):
    """
    Create generator of values in a NAF files, e.g.,
    all lemmas that are pos="NOUN"

    :param lxml.etree._ElementTree doc: result of etree.parse(PATH)
    :param xml_path: e.g., terms/term
    :param list attribute: list of attributes to concatenate, e.g., ["lemma"] or ["lemma", "pos"]
    :param dict attr_requirements: whether you want other attributes of the
    same element to have a specific value, e.g, {"pos": {"NOUN"}}

    :rtype: generator
    :return generator of values
    """
    for el in doc.xpath(xml_path):

        el_attributes = el.attrib

        to_add = True

        for req_attr, ok_values in attr_requirements.items():
            el_attr_value = el_attributes[req_attr]
            assert req_attr in el_attributes, f'required attribute not part of element attributes: {attributes}'
            if el_attr_value not in ok_values:
                if verbose >= 2:
                    print(f'skipping element because {req_attr} has value {el_attr_value}')
                to_add = False

        if not to_add:
            continue

        values = [el.get(attr)
                  for attr in selected_attributes]
        the_value = '--'.join(values)
        yield the_value

def get_naf_paths(inc_coll_obj,
                  main_naf_folder,
                  verbose=0):
    """

    :param inc_coll_obj:
    :param str main_naf_folder: folder where NAF files are stored,
    usually called wik_output with subfolders en, nl and it
    :param verbose:
    :return:
    """
    naf_paths = set()
    naf_to_inc_id = {}
    for inc_obj in inc_coll_obj.incidents:
        for ref_text_obj in inc_obj.reference_texts:
            naf_path = os.path.join(main_naf_folder,
                                    ref_text_obj.language,
                                    f'{ref_text_obj.name}.naf')
            if os.path.exists(naf_path):
                naf_paths.add(naf_path)
                naf_to_inc_id[naf_path] = f'{WIKIDATA_PREFIX}{inc_obj.wdt_id}'

    if verbose >= 2:
        print()
        print(f'found {len(naf_paths)} NAF paths')

    return naf_paths, naf_to_inc_id

def add_wd_uris_to_naf_file(naf_path,
                            wiki_to_wd,
                            pass_if_coreferences_el_exists=True,
                            verbose=0):
    """

    :param naf_path:
    :param wiki_to_wd:
    :return:
    """
    parser = etree.XMLParser(remove_blank_text=True)
    doc = etree.parse(naf_path, parser)
    changed = False

    if pass_if_coreferences_el_exists:
        coreferences_header_el = doc.find('nafHeader/linguisticProcessors[@layer="coreferences"]')
        if coreferences_header_el is not None:
            if verbose >= 5:
                print(f'skipped {naf_path} since it already contains coreferences layer.')
            return

    for ext_refs_el in doc.xpath('entities/entity/externalReferences'):
        ext_ref_els = list(ext_refs_el.xpath('externalRef'))

        all_refs = {ext_ref_el.get('reference')
                    for ext_ref_el in ext_ref_els}

        for ext_ref_el in ext_ref_els:
            wiki_reference = ext_ref_el.get('reference')
            wd_reference = wiki_to_wd.get(wiki_reference, None)

            if all([wd_reference is not None,
                    wd_reference not in all_refs]):

                # add externalRef element
                new_ext_ref_el = etree.SubElement(ext_refs_el, 'externalRef')
                new_ext_ref_el.set('reference', wiki_to_wd[wiki_reference])
                new_ext_ref_el.set('source', ext_ref_el.get('source'))
                new_ext_ref_el.set('timestamp', ext_ref_el.get('timestamp'))
                new_ext_ref_el.set('resource', ext_ref_el.get('resource'))

                ext_ref_els.append(new_ext_ref_el)
                all_refs.add(wd_reference)

                changed = True

        all_refs = [ext_ref_el.get('reference')
                    for ext_ref_el in ext_ref_els]
        assert len(all_refs) == len(set(all_refs)), f'duplicate references in {naf_path}'

    # overwrite NAF file
    if changed:
        doc.write(naf_path,
                  encoding = 'utf-8',
                  pretty_print = True,
                  xml_declaration = True)

        if verbose >= 4:
            print(f'add links to {naf_path}')


def add_coreferences_layer(naf_path,
                           uri_to_rels,
                           wd_uris_of_inc_id,
                           pass_if_coreferences_el_exists=True,
                           verbose=0):
    """

    :param str naf_path: NAF file with entities layer
    and without coreferences layer
    :param verbose:
    """
    parser = etree.XMLParser(remove_blank_text=True)
    doc = etree.parse(naf_path, parser)
    root = doc.getroot()

    if pass_if_coreferences_el_exists:
        coreferences_header_el = doc.find('nafHeader/linguisticProcessors[@layer="coreferences"]')
        if coreferences_header_el is not None:
            if verbose >= 5:
                print(f'skipped {naf_path} since it already contains coreferences layer.')
            return

    added = False

    # extract wd_uri -> set of spans
    wd_uri_to_spans = defaultdict(list)
    for entity_el in doc.xpath('entities/entity'):
        target_ids = [target.get('id')
                      for target in entity_el.xpath('span/target')]
        for ext_ref_el in entity_el.xpath('externalReferences/externalRef'):
            reference = ext_ref_el.get('reference')

            if all([reference.startswith(WIKIDATA_PREFIX), # is Wikidata link
                    reference in wd_uris_of_inc_id         # is part of structured data
                    ]):
                if target_ids not in wd_uri_to_spans[reference]:
                    wd_uri_to_spans[reference].append(target_ids)

    if not wd_uri_to_spans:
        return added

    # add coreferences header
    naf_header_el = doc.find('nafHeader')
    ent_lp_el = naf_header_el.find('linguisticProcessors[@layer="entities"]/lp')
    coreferences_header_el = etree.Element(_tag='linguisticProcessors',
                                           attrib={'layer': 'coreferences'})

    coreferences_lp_el = etree.Element(_tag='lp',
                                       attrib={
                                           'beginTimestamp' : ent_lp_el.get('beginTimestamp'),
                                           'endTimestamp' : ent_lp_el.get('endTimestamp'),
                                           'name' : ent_lp_el.get('name'),
                                           'id' : COREFERENCES_ID,
                                           'version' : ent_lp_el.get('version')
                                       })
    # add coreferences layer
    coreferences_el = etree.Element(_tag='coreferences')
    naf_header_el.append(coreferences_lp_el)

    naf_header_el.append(coreferences_header_el)
    coreferences_header_el.append(coreferences_lp_el)



    for index, (wd_uri, spans) in enumerate(wd_uri_to_spans.items(),
                                            1):


        q_id = wd_uri.replace(WIKIDATA_PREFIX, '')
        sem_rels = uri_to_rels[q_id]

        if not sem_rels:
            continue

        if len(sem_rels) >= 2:
            if verbose:
                print(f'ignoring uri: {wd_uri}')
                print(f'it has 2 or more sem rels: {sem_rels}')
            continue

        sem_rel = list(sem_rels)[0]
        if sem_rel == 'http://semanticweb.cs.vu.nl/2009/11/sem/Event':
            coref_type = 'event'
        else:
            coref_type = 'entity'

        # coref element
        coref_el = etree.Element(_tag='coref',
                                 attrib={
                                     'id' : f'co{index}',
                                     'status' : 'system',
                                     'type' : coref_type
                                 })


        for span in spans:
            span_el = etree.Element(_tag='span',
                                    attrib={
                                        'status': 'system'
                                    })

            for target_id in span:
                target_el = etree.Element(_tag='target',
                                          attrib={
                                          'id' : target_id
                                      })
            span_el.append(target_el)

            coref_el.append(span_el)

        ext_refs_el = etree.Element(_tag='externalReferences')
        new_ext_ref_el = etree.Element(_tag='externalRef',
                                       attrib={
                                           'reference' : wd_uri,
                                           'resource' : 'http://www.wikidata.org',
                                           'source' : COREFERENCES_ID,
                                           'reftype' : sem_rel,
                                           'timestamp' : ent_lp_el.get('endTimestamp')
                                       })

        ext_refs_el.append(new_ext_ref_el)

        coref_el.append(ext_refs_el)
        coreferences_el.append(coref_el)

    root.append(coreferences_el)
    added = True

    # overwrite NAF file
    doc.write(naf_path,
              encoding='utf-8',
              pretty_print=True,
              xml_declaration=True)

    if verbose >= 4:
        print(f'add links to {naf_path}')

    return added


def add_wikidata_uris_to_naf_files(inc_coll_obj,
                                   main_naf_folder,
                                   languages,
                                   verbose=0):
    """

    :param inc_coll_obj:
    :return:
    """
    # get NAF paths
    naf_paths, naf_to_inc_id = get_naf_paths(inc_coll_obj,
                                             main_naf_folder,
                                             verbose=verbose)

    # get uris
    uri_to_rels, inc_id_to_wd_uris = utils.get_uris(inc_coll_obj,
                                                    verbose=verbose)

    # get mapping Wikidata <-> Wikipedia
    wd_to_wiki,\
    wiki_to_wd = native_api_utils.map_wd_uri_to_wikipedia_uri(uri_to_rels,
                                                              languages,
                                                              verbose=verbose)

    # add entity links to NAF files
    for naf_path in naf_paths:
        add_wd_uris_to_naf_file(naf_path,
                                wiki_to_wd,
                                verbose=verbose)

    # add links to coreferences elements
    nafs_with_coref = 0
    for naf_path in naf_paths:

        inc_id = naf_to_inc_id[naf_path]
        wd_uris_of_inc_id = inc_id_to_wd_uris[inc_id]

        result = add_coreferences_layer(naf_path,
                                        uri_to_rels,
                                        wd_uris_of_inc_id,
                                        verbose=verbose)
        if result:
            nafs_with_coref += 1

    if verbose >= 2:
        print()
        print(f'added coreferences layer to {nafs_with_coref} NAF files.')
