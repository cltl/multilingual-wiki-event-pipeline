import json
from collections import defaultdict, Counter
from rdflib.namespace import Namespace
from rdflib.namespace import RDF, RDFS
from rdflib import Graph
from rdflib import URIRef, BNode, Literal, XSD

class IncidentCollection:
    
    def __init__(self,
                incident_type,
                languages,
                incidents=[],
                ):
        self.incident_type=incident_type
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

        num_with_sources=0
        sum_sources=0
        
        countries=[]
        num_languages=[]

        extra_info_dists=defaultdict(list)
        count_occurences=defaultdict(int)

        found_bys=[]

        num_incidents=len(self.incidents)
        for incident in self.incidents:
            for ref_text in incident.reference_texts:
                if ref_text.wiki_content:
                    num_with_wikipedia+=1
                if len(ref_text.sources):
                    num_with_sources+=1
                    sum_sources+=len(ref_text.sources)
                found_bys.append('|'.join(ref_text.found_by))
            if len(incident.reference_texts)==3:
                print(incident.wdt_id)
            num_languages.append(len(incident.reference_texts))
            if 'sem:hasPlace' in incident.extra_info.keys():
                for country in incident.extra_info['sem:hasPlace']:
                    countries.append(country)
            for p, v in incident.extra_info.items():
                if isinstance(v, set):
                    for value in v:
                        extra_info_dists[p].append(value)
                else:
                    extra_info_dists[p].append(v)
                count_occurences[p]+=1
        if num_with_sources: 
            avg_sources=sum_sources/num_with_sources
        else:
            avg_sources=0
        countries_dist=Counter(countries).most_common(10)
        numlang_dist=Counter(num_languages)
        
        extra_info_dist_agg={}
        for k, v in extra_info_dists.items():
            extra_info_dist_agg[k]=Counter(v).most_common(10)

        return num_incidents, num_with_wikipedia, Counter(found_bys), num_with_sources, avg_sources, countries_dist, numlang_dist, extra_info_dist_agg,count_occurences
    
    def serialize(self, filename=None):
        """
        Serialize a collection of incidents to a .ttl file.
        """
    
        with open('wdt_fn_mappings/change_of_leadership.json', 'rb') as r:
            wdt_fn_mappings_COL=json.load(r)     

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
        election=URIRef('https://www.wikidata.org/wiki/Q40231')
        election_label=Literal('election')
        country_label=Literal('country')
        
        for incident in self.incidents:
            event_id = URIRef('http://www.wikidata.org/entity/%s' % incident.wdt_id)

            # event labels in all languages
            for ref_text in incident.reference_texts:
                name_in_lang=Literal(ref_text.name, lang=ref_text.language)
                g.add(( event_id, RDFS.label, name_in_lang))

                # denotation of the event
                wikipedia_article=URIRef(ref_text.wiki_uri)
                g.add(( event_id, GRASP.denotedIn, wikipedia_article ))
                g.add(( wikipedia_article, DCT.description, Literal(ref_text.wiki_content) ))
                g.add(( wikipedia_article, DCT.title, Literal(ref_text.name) ))
                g.add(( wikipedia_article, DCT.language, Literal(ref_text.language) ))
                g.add(( wikipedia_article, DCT.type, URIRef('http://purl.org/dc/dcmitype/Text') ))
                for source in ref_text.sources:
                    g.add(( wikipedia_article, DCT.source, URIRef(source) ))        

            # event type information
            g.add( (event_id, RDF.type, SEM.Event) )
            g.add(( event_id, SEM.eventType, election))

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
                        if pid not in {'hasTimeStamp', 'time'}:
                            an_obj=URIRef(v)
                        else:
                            an_obj=Literal(v,datatype=XSD.date)
                        g.add(( event_id, RES[pid], an_obj))

            # time information
            #timestamp=Literal(incident.time)
            #g.add((event_id, SEM.hasTimeStamp, timestamp))

            # place information
            #country=URIRef(incident.country_id)
            #country_name=Literal(incident.country_name)
            #g.add((event_id, SEM.hasPlace, country))
            #g.add((country, RDFS.label, country_name))
            #g.add((country, RDF.type, WDT_ONT.Q6256))

        g.add((election, RDFS.label, election_label))
        #g.add((country, RDFS.label, country_label))

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
                wiki_uri='',
                name='',
                wiki_content='',
                html_content='',
                language='',
                creation_date='',
                authors=[],
                sources='',
                langlinks=[],
                found_by=''):
        self.name=name
        self.wiki_uri=wiki_uri
        self.wiki_content=wiki_content
        self.html_content=html_content
        self.language=language
        self.creation_date=creation_date
        self.authors=authors
        self.sources=sources
        self.langlinks=langlinks
        self.found_by=found_by
