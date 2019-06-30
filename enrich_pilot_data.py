import classes

from collections import namedtuple
import pickle
import shutil
from path import Path
import os.path
import spacy_to_naf
import xml.etree.ElementTree as ET
from lxml import etree
from datetime import datetime
import wikitextparser as wtp
import sys 

EntityElement = namedtuple('EntityElement', ['eid', 'entity_type', 'targets', 'text', 'ext_refs'])

def find_next_occurrence(sf, min_token_id, t_layer, doc):
    if not len(sf): return [], min_token_id
    tokens=t_layer.findall('wf')
    for w in tokens:
        if min_token_id>int(w.get('id').replace('w', '')): continue
        if w.text==sf[0]:
            current_id=w.get('id')
            int_id=int(current_id.replace('w', ''))
            if len(sf)==1:
                ret_tokens=[current_id]
                min_token_id=int_id
                return ret_tokens, min_token_id
            else:
                fits=True
                ret_tokens=[]
                print(sf)
                for i in range(1, len(sf)):
                    sf[i]=sf[i].strip()
                    next_token=doc.findall("//wf[@id='w%d']" % (int_id+i))[0]
                    token_text=next_token.text
                    if not token_text or token_text!=sf[i]:
                        print(next_token.text, sf[i])
                        fits=False
                        break
                    last_id=next_token.get('id')
                    last_int_id=int(last_id.replace('w', ''))
                    ret_tokens.append(last_id)
                if fits:
                    print('fits')
                    min_token_id=last_int_id
                    return ret_tokens, min_token_id
    return [], min_token_id

def shift_all(links_json, x):
    new_json={}
    for start, end in links_json.keys():
        new_start=start-x
        new_end=end-x
        new_json[tuple([new_start, new_end])]=links_json[(start, end)]
    return new_json

def get_text_and_links(wikitext):
    parsed = wtp.parse(wikitext)
    basic_info=parsed.sections[0]
    saved_links={}
    for link in basic_info.wikilinks:
        original_span=link.span
        if not original_span or original_span[0]==-1: continue
        start=original_span[0]
        end=original_span[1]
        target=link.target
        text=link.text
        if not text: text=target
        basic_info[original_span[0]:original_span[1]]=text
        move_to_left=end-start-len(text)
        saved_links=shift_all(saved_links, move_to_left)
        new_end=end-move_to_left
        saved_links[tuple([start, new_end])]=(text, target)

    return basic_info, saved_links

def add_entity_element(entities_layer, entity_data, add_comments=False):
    """
    Function that adds an entity element (with links) to the entity layer.
    """
    entity_el = etree.SubElement(entities_layer, "entity")
    entity_el.set("id", entity_data.eid)
    entity_el.set("type", entity_data.entity_type)
    references_el = etree.SubElement(entity_el, "references")
    span = etree.SubElement(references_el, "span")
    if add_comments:
        span.append(etree.Comment(' '.join(entity_data.text)))
    for target in entity_data.targets:
        target_el = etree.SubElement(span, "target")
        target_el.set("id", target)
    ext_refs_el = etree.SubElement(entity_el, 'externalReferences')
    for ext_ref in entity_data.ext_refs:
        one_ext_ref_el=etree.SubElement(ext_refs_el, 'externalRef')
        one_ext_ref_el.set("reference", ext_ref)

pilot_folder='pilot_data'
input_incidents_file='bin/murder_nl,it,en,pilot.bin'
input_incidents_file='bin/election_nl,it,ja,en,pilot.bin'
input_folder='%s/naf' % pilot_folder
output_folder=Path('%s/naf_with_entities' % pilot_folder)

if output_folder.exists():
    shutil.rmtree(str(output_folder))
output_folder.mkdir()

with open(input_incidents_file, 'rb') as f:
    collection=pickle.load(f)

modelname='wikilinks'
modelversion='v1'
start_time = spacy_to_naf.time_in_correct_format(datetime.now())
end_time = spacy_to_naf.time_in_correct_format(datetime.now())

count_outfiles=0
count_infiles=0
count_entities=0
for incident in collection.incidents:
    for ref_text in incident.reference_texts:
        in_naf_filename='%s/%s.naf' % (input_folder, ref_text.name)
        if os.path.isfile(in_naf_filename):
            count_infiles+=1
            print(in_naf_filename)

            naf_output_path = str(output_folder / f'{ref_text.name}.naf')

            doc=etree.parse(in_naf_filename)
            root=doc.getroot()
            naf_header = root.find("nafHeader")
            ling_proc=etree.SubElement(naf_header, 'linguisticProcessors')
            ling_proc.set("layer", 'entities')
            lp = etree.SubElement(ling_proc, "lp")
            lp.set("beginTimestamp", start_time)
            lp.set('endTimestamp', end_time)
            lp.set('name', modelname)
            lp.set('version', modelversion)

            entities_layer = etree.SubElement(root, "entities")

            try:
                sec0=ref_text.text_and_links['*']
            except Exception as e:
                if naf_output_path is not None:
                    with open(naf_output_path, 'w') as outfile:
                        outfile.write(spacy_to_naf.NAF_to_string(NAF=root))
                continue

            info, links=get_text_and_links(sec0)
            print(links)

            t_layer = root.find("text")
            min_token_id=1
            next_id=1
            for offset, value in links.items():
                text=value[0]
                sfs=text.split()
                target=value[1]
                ret_tokens, min_token_id=find_next_occurrence(sfs, min_token_id, t_layer, doc)
                if ret_tokens:
                    entity_data=EntityElement(
			     eid='e%d' % next_id,
			     entity_type='UNK',
			     text=text,
			     targets=ret_tokens, # TODO: MAP TOKENS TO TERMS
			     ext_refs=[target])
                    add_entity_element(entities_layer, entity_data, add_comments=True)
                    count_entities+=1
                    next_id+=1

            if naf_output_path is not None:
                with open(naf_output_path, 'w') as outfile:
                    outfile.write(spacy_to_naf.NAF_to_string(NAF=root))
                    count_outfiles+=1

    print('Input NAFs', count_infiles)
    print('Output NAFs', count_outfiles)
    print('Count entities', count_entities)
