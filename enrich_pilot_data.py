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

EntityElement = namedtuple('EntityElement', ['eid', 'entity_type', 'targets', 'text', 'ext_refs'])


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

for incident in collection.incidents:
    for ref_text in incident.reference_texts:
        in_naf_filename='%s/%s.naf' % (input_folder, ref_text.name)
        if os.path.isfile(in_naf_filename):
            print(in_naf_filename)
            root=etree.parse(in_naf_filename).getroot()
            naf_header = root.find("nafHeader")
            ling_proc=etree.SubElement(naf_header, 'linguisticProcessors')
            ling_proc.set("layer", 'entities')
            lp = etree.SubElement(ling_proc, "lp")
            lp.set("beginTimestamp", start_time)
            lp.set('endTimestamp', end_time)
            lp.set('name', modelname)
            lp.set('version', modelversion)

            entities_layer = etree.SubElement(root, "entities")

            entities_layer = etree.SubElement(root, "entities")
            entity_data=EntityElement(
			     eid='e1',
			     entity_type='PER',
			     text='John Cash',
			     targets=['t1', 't2'],
			     ext_refs=['http://example.org/John'])
            add_entity_element(entities_layer, entity_data)

            naf_output_path = str(output_folder / f'{ref_text.name}.naf')

            if naf_output_path is not None:
                with open(naf_output_path, 'w') as outfile:
                    outfile.write(spacy_to_naf.NAF_to_string(NAF=root))
