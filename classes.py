import json
from collections import defaultdict, Counter, OrderedDict
from rdflib.namespace import Namespace
from rdflib.namespace import RDF, RDFS
from rdflib import Graph
from rdflib import URIRef, BNode, Literal, XSD
from scipy import stats
import numpy as np
import networkx as nx

eventtype2json={}

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

    def compute_stats(self, verbose=0):
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

        direct_types=[]

        countries=[]
        num_wikis=[]
        num_languages=defaultdict(int)

        extra_info_dists=defaultdict(list)
        count_occurences=defaultdict(int)
        count_values=defaultdict(int)

        found_bys=[]

        all_info=0

        if self.incident_type in eventtype2json.keys():
            jsonfilename='wdt_fn_mappings/%s.json' % eventtype2json[self.incident_type]
        else:
            jsonfilename='wdt_fn_mappings/any.json'

        with open(jsonfilename, 'rb') as f:
            wdt_fn_mappings_COL=json.load(f)

        all_frame_elements=set(wdt_fn_mappings_COL.keys())

        num_incidents=len(self.incidents)
        for incident in self.incidents:
            langs=set()
            if verbose >= 1:
                print('incident ID: ', incident.wdt_id)
            for ref_text in incident.reference_texts:
                if verbose >= 1:
                    print('URI', ref_text.uri)
                if ref_text.content:
                    if verbose >= 1:
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

            if isinstance(incident.direct_types, set):
                for value in incident.direct_types:
                    direct_types.append(value)
            else:
                direct_types.append(incident.direct_types)

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

        return num_incidents, num_with_wikipedia, Counter(found_bys), Counter(direct_types), num_with_prim_rt, num_with_annotations, desc_prim_rt, cntr_prim_rt, countries_dist, numwiki_dist, num_languages, extra_info_dist_agg, count_occurences, count_values, all_info


    def event_expressions_or_meanings_distribution(self, event_type, lang, 
                                                   add_descendants=False, verbose=0):
        """

        :param list event_types: list of event type
        :param str lang: nl | en | it
        :param bool add_descendants: if True, also include all descendants via the subclass of relation
        """
        wdt_ids = self.event_type2wdt_ids[event_type]

        the_descendants = set()
        if add_descendants:
            the_descendants = self.direct_type2descendants[event_type]
            descendants_wdt_ids = set()
            for the_descendant in the_descendants:
                descendants_wdt_ids.update(self.event_type2wdt_ids.get(the_descendant, set()))

            wdt_ids.update(descendants_wdt_ids)

        if verbose >= 2:
            print(f'found {len(wdt_ids)} incidents for {event_type}')
            if add_descendants:
                print(f'found {len(the_descendants)} different descendant event types') 
                print(f'number of incidents in descendants: {len(descendants_wdt_ids)}')
            

        naf_coll_obj = naf_classes.NAF_collection()
        for incident_obj in self.incidents:
            if incident_obj.wdt_id in wdt_ids:
                for ref_text_obj in incident_obj.reference_texts:
                    if ref_text_obj.language == lang:
                        if ref_text_obj.naf is not None:
                            naf_coll_obj.add_naf_objects([ref_text_obj.naf])

        naf_coll_obj.merge_distributions('terms')
        naf_coll_obj.merge_distributions('predicates')

        return naf_coll_obj

    def serialize(self, filename=None):
        """
        Serialize a collection of incidents to a .ttl file.
        """

        if self.incident_type in eventtype2json.keys():
            jsonfilename='wdt_fn_mappings/%s.json' % eventtype2json[self.incident_type]
        else:
            jsonfilename='wdt_fn_mappings/any.json'

        print(jsonfilename)
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

    def get_index_event_type2wdt_ids(self):
        event_type2wdt_ids = defaultdict(set)
        for incident_obj in self.incidents:
            for direct_type in incident_obj.direct_types:
                event_type2wdt_ids[direct_type].add(incident_obj.wdt_id)

        return event_type2wdt_ids



class Incident:

    def __init__(self,
                incident_type,
                wdt_id,
                reference_texts=[],
                extra_info={},
                direct_types=set()):
        self.incident_type=incident_type
        self.wdt_id=wdt_id
        self.reference_texts=reference_texts
        self.extra_info=extra_info
        self.direct_types=direct_types

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
                annotations=[]):
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
