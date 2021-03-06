import spacy
import sys
from collections import namedtuple, Counter
import pickle
import shutil
from pathlib import Path
import os.path
import spacy_to_naf
import xml.etree.ElementTree as ET
from lxml import etree
from datetime import datetime
import wikitextparser as wtp
import xml_utils

EntityElement = namedtuple('EntityElement', ['eid', 'entity_type', 'targets', 'text', 'ext_refs'])

def remove_templates_on_top(text):
    lines=text.split('\n')
    my_text=[]
    for l in lines:
        template=l.startswith('|') or l.startswith('{{') or l.startswith('}}')
        if not template:
            my_text.append(l)
    return '\n'.join(my_text)

def find_next_occurrence(sf, min_token_id, t_layer, doc):
    if not len(sf): return [], min_token_id
    tokens=t_layer.findall('wf')
    for w in tokens:
        if min_token_id>int(w.get('id').replace('w', '')): continue
        if w.text==sf[0]:
            current_id=w.get('id')
            int_id=int(current_id.replace('w', ''))
            ret_tokens=[current_id]
            if len(sf)==1:
                min_token_id=int_id
                return ret_tokens, min_token_id
            else:
                fits=True
                for i in range(1, len(sf)):
                    sf[i]=sf[i].strip()
                    next_token=doc.findall("//wf[@id='w%d']" % (int_id+i))[0]
                    token_text=next_token.text
                    if not token_text or token_text!=sf[i]:
                        fits=False
                        break
                    last_id=next_token.get('id')
                    last_int_id=int(last_id.replace('w', ''))
                    ret_tokens.append(last_id)
                if fits:
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


def load_mapping_tokens_to_terms(): pass

pilot_folder='pilot_data'
input_folder='%s/naf' % pilot_folder
output_folder=Path('%s/naf_with_entities' % pilot_folder)

if output_folder.exists():
    shutil.rmtree(str(output_folder))
output_folder.mkdir()

eventtype_and_binfile = [
     ('murder', 'bin/murder_nl,it,en,pilot.bin'),
     ('election', 'bin/election_nl,it,en,pilot.bin')
]
spacy_models={'en': spacy.load('en_core_web_sm') ,
              'nl' : spacy.load('nl_core_news_sm') ,
              'it': spacy.load('it_core_news_sm')}

modelname='wikilinks'
modelversion='v1'
start_time = spacy_to_naf.time_in_correct_format(datetime.now())
end_time = spacy_to_naf.time_in_correct_format(datetime.now())

for eventtype, binfile in eventtype_and_binfile:
    count_outfiles=0
    count_infiles=0
    count_entities=0
    count_per_doc=[]
    initial_links=0
    with open(binfile, 'rb') as f:
        collection = pickle.load(f)
    print(len(collection.incidents))
    for incident in collection.incidents:
        for ref_text in incident.reference_texts:
            in_naf_filename='%s/%s.naf' % (input_folder, ref_text.name)
            if os.path.isfile(in_naf_filename):
                count_infiles+=1
    #            if ref_text.name!='2009 Icelandic parliamentary election':
    #                continue

                naf_output_path = str(output_folder / f'{ref_text.name}.naf')

                parser = etree.XMLParser(remove_blank_text=True)
                doc=etree.parse(in_naf_filename, parser)

                wid2tid = xml_utils.mapping_wid2tid(doc)

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
                    sec0=ref_text.wiki_text_and_links['*']
                except Exception as e:
                    if naf_output_path is not None:
                        with open(naf_output_path, 'w') as outfile:
                            outfile.write(spacy_to_naf.NAF_to_string(NAF=root))
                    continue
                clean_sec0=remove_templates_on_top(sec0)
                info, links=get_text_and_links(clean_sec0)

                t_layer = root.find("text")
                min_token_id=1
                next_id=1
                initial_links+=len(links.items())
                for offset, value in links.items():
                    text=value[0]
                    spacy_model=spacy_models[ref_text.language]
                    #spacy_model=spacy.load(lang_model)
                    with_spacy=spacy_model(text)
                    sfs = [t.text for t in with_spacy]
                    target=value[1]
                    ret_tokens, min_token_id=find_next_occurrence(sfs, min_token_id, t_layer, doc)

                    t_ids = [wid2tid[wid] for wid in ret_tokens]

                    if ret_tokens:
                        entity_data=EntityElement(
                     eid='e%d' % next_id,
                     entity_type='UNK',
                     text=text,
                     targets=t_ids,
                     ext_refs=[{'reference': target}])
                        spacy_to_naf.add_entity_element(entities_layer, entity_data, add_comments=True)
                        count_entities+=1
                        next_id+=1

                count_per_doc.append(next_id-1)
                if naf_output_path is not None:
                    with open(naf_output_path, 'w') as outfile:
                        outfile.write(spacy_to_naf.NAF_to_string(NAF=root))
                        count_outfiles+=1

    print('Input NAFs', count_infiles)
    print('Output NAFs', count_outfiles)
    print('Count entities', count_entities)
    print('Count initial seed', initial_links)
    dist_links=Counter(count_per_doc)
    print('Distribution of entity links over files', dict(sorted(dist_links.items())))
