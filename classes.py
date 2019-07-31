import json
from collections import defaultdict, Counter, OrderedDict
from rdflib.namespace import Namespace
from rdflib.namespace import RDF, RDFS
from rdflib import Graph
from rdflib import URIRef, BNode, Literal, XSD
from scipy import stats
import numpy as np

import spacy_to_naf

eventtype2json={'election': 'change_of_leadership', 'murder': 'killing'}

class IncidentCollection:
    
    def __init__(self,
                incident_type,
                incident_type_uri,
                languages,
                incidents=[],
                ):
        self.incident_type=incident_type
        self.incident_type_uri=incident_type_uri
        self.languages=languages
        self.incidents=incidents
        
    
    def compute_stats(self):
        """
        Compute statistics on the incident collection.
        """
        
        num_with_wikipedia=0
        wiki_from_both_methods=0
        wiki_from_api_only=0
        wiki_from_sparql_only=0

        num_with_prim_rt=0
        num_prim_rt=[]
        num_with_annotations=0       
 
        countries=[]
        num_wikis=[]
        num_languages=defaultdict(int)

        extra_info_dists=defaultdict(list)
        count_occurences=defaultdict(int)
        count_values=defaultdict(int)

        found_bys=[]

        all_info=0

        jsonfilename='wdt_fn_mappings/%s.json' % eventtype2json[self.incident_type]

        with open(jsonfilename, 'rb') as f:
            wdt_fn_mappings_COL=json.load(f)

        all_frame_elements=set(wdt_fn_mappings_COL.keys())

        num_incidents=len(self.incidents)
        for incident in self.incidents:
            langs=set()
            print('incident ID: ', incident.wdt_id)
            for ref_text in incident.reference_texts:
                print('URI', ref_text.uri)
                if ref_text.content:
                    print(ref_text.name, ', FOUND BY: ', ref_text.found_by)
                    num_with_wikipedia+=1
                if len(ref_text.primary_ref_texts):
                    num_with_prim_rt+=1
                num_prim_rt.append(len(ref_text.primary_ref_texts))
                if len(ref_text.annotations):
                    num_with_annotations+=1
                found_bys.append('|'.join(ref_text.found_by))

                langs.add(ref_text.language)
            sorted_langs=tuple(sorted(list(langs)))
            num_languages[sorted_langs]+=1

            num_wikis.append(len(incident.reference_texts))
            if 'sem:hasPlace' in incident.extra_info.keys():
                for country in incident.extra_info['sem:hasPlace']:
                    countries.append(country)
            extra_info_keys=set(incident.extra_info.keys())
            if extra_info_keys==all_frame_elements:
                all_info+=1
            for p, v in incident.extra_info.items():
                if isinstance(v, set):
                    for value in v:
                        extra_info_dists[p].append(value)
                    count_values[p]+=len(v)
                else:
                    extra_info_dists[p].append(v)
                    count_values[p]+=1
                count_occurences[p]+=1
        if num_with_prim_rt: 
            desc_prim_rt=stats.describe(np.array(num_prim_rt))
            cntr_prim_rt=Counter(num_prim_rt)
            cntr_prim_rt = dict(sorted(cntr_prim_rt.items()))
        else:
            desc_prim_rt=None
            cntr_prim_rt=None
        countries_dist=Counter(countries).most_common(10)
        numwiki_dist=Counter(num_wikis)
        
        extra_info_dist_agg={}
        for k, v in extra_info_dists.items():
            extra_info_dist_agg[k]=Counter(v).most_common(10)

        return num_incidents, num_with_wikipedia, Counter(found_bys), num_with_prim_rt, num_with_annotations, desc_prim_rt, cntr_prim_rt, countries_dist, numwiki_dist, num_languages, extra_info_dist_agg, count_occurences, count_values, all_info
    
    def serialize(self, filename=None):
        """
        Serialize a collection of incidents to a .ttl file.
        """

        jsonfilename='wdt_fn_mappings/%s.json' % eventtype2json[self.incident_type]

        with open(jsonfilename, 'rb') as f:
            wdt_fn_mappings_COL=json.load(f)

        g = Graph()
        
        # Namespaces definition
        SEM=Namespace('http://semanticweb.cs.vu.nl/2009/11/sem/')
        WDT_ONT=Namespace('http://www.wikidata.org/wiki/')
        GRASP=Namespace('http://groundedannotationframework.org/grasp#')
        DCT=Namespace('http://purl.org/dc/elements/1.1/')
        FN=Namespace('http://premon.fbk.eu/resource/fn17-')
        PREMON=Namespace('https://premon.fbk.eu/resource/')
        g.bind('sem', SEM)
        g.bind('wdt', WDT_ONT)
        g.bind('grasp', GRASP)
        g.bind('dct', DCT)
        g.bind('fn17', FN)
        g.bind('pm', PREMON)

        # Some core URIs/Literals
        inc_type_literal=Literal(self.incident_type)
        inc_type_uri=URIRef(self.incident_type_uri)

        country_literal=Literal('country')
        
        for incident in self.incidents:
            event_id = URIRef('http://www.wikidata.org/entity/%s' % incident.wdt_id)

            # event labels in all languages
            for ref_text in incident.reference_texts:
                name_in_lang=Literal(ref_text.name, lang=ref_text.language)
                g.add(( event_id, RDFS.label, name_in_lang))

                # denotation of the event
                wikipedia_article=URIRef(ref_text.uri)
                g.add(( event_id, GRASP.denotedIn, wikipedia_article ))
                g.add(( wikipedia_article, DCT.description, Literal(ref_text.content) ))
                g.add(( wikipedia_article, DCT.title, Literal(ref_text.name) ))
                g.add(( wikipedia_article, DCT.language, Literal(ref_text.language) ))
                g.add(( wikipedia_article, DCT.type, URIRef('http://purl.org/dc/dcmitype/Text') ))
                for source in ref_text.primary_ref_texts:
                    g.add(( wikipedia_article, DCT.source, URIRef(source) ))        

            # event type information
            g.add( (event_id, RDF.type, SEM.Event) )
            g.add(( event_id, SEM.eventType, inc_type_uri))

            # Linking to FN1.7 @ Premon
            g.add(( event_id, RDF.type, FN.change_of_leadership ))

            # Map all roles to FN roles
            for predicate, wdt_prop_paths in wdt_fn_mappings_COL.items():
                if predicate in incident.extra_info.keys():
                    vals=incident.extra_info[predicate]
                    prefix, pid=predicate.split(':')
                    if prefix=='sem':
                        RES=SEM
                    else:
                        RES=PREMON
                    for v in vals:
                        v=(v.split('|')[0]).strip()
                        if pid not in {'hasTimeStamp', 'time'}:
                            an_obj=URIRef(v)
                        else:
                            if v.endswith('-01-01T00:00:00Z'):
                                vyear=v[:4]
                                an_obj=Literal(vyear, datatype=XSD.gYear)
                            else:
                                an_obj=Literal(v,datatype=XSD.date)
                        g.add(( event_id, RES[pid], an_obj))

        g.add((inc_type_uri, RDFS.label, inc_type_literal))

        # Done. Store the resulting .ttl file now...
        if filename: # if a filename was supplied, store it there
            g.serialize(format='turtle', destination=filename)
        else: # else print to the console
            print(g.serialize(format='turtle'))

class Incident:

    def __init__(self, 
                incident_type,
                wdt_id,
                reference_texts=[],
                extra_info={}):
        self.incident_type=incident_type
        self.wdt_id=wdt_id
        self.reference_texts=reference_texts
        self.extra_info=extra_info

class ReferenceText:
    
    def __init__(self,
                uri='',
                web_archive_uri='',
                name='',
                content='',
                raw_content='',
                language='',
                creation_date='',
                authors=[],
                primary_ref_texts='',
                wiki_langlinks=[],
                found_by='',
                annotations=None):
        self.name=name
        self.uri=uri
        self.web_archive_uri=web_archive_uri
        self.content=content
        self.raw_content=raw_content
        self.language=language
        self.creation_date=creation_date
        self.authors=authors
        self.primary_ref_texts=primary_ref_texts
        self.wiki_langlinks=wiki_langlinks
        self.found_by=found_by
        self.annotations=annotations

    def process_spacy_and_convert_to_naf(self,
                                         nlp,
                                         dct, # in a next iteration, we can make this a class attribute
                                         layers,
                                         output_path=None):
        """
        process with spacy and convert to NAF

        :param nlp: spacy language model
        :param datetime.datetime dct: document creation time
        :param set layers: layers to convert to NAF, e.g., {'raw', 'text', 'terms'}
        :param output_path: if provided, NAF is saved to that file

        :return: the root of the NAF XML object
        """
        root = spacy_to_naf.text_to_NAF(text=self.content,
                                        nlp=nlp,
                                        dct=dct,
                                        layers=layers,
                                        title=self.name,
                                        uri=self.uri,
                                        language=self.language)

        if output_path is not None:
            with open(output_path, 'w') as outfile:
                outfile.write(spacy_to_naf.NAF_to_string(NAF=root))

        return root
