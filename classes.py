from collections import Counter
from rdflib.namespace import Namespace
from rdflib.namespace import RDF, RDFS
from rdflib import Graph
from rdflib import URIRef, BNode, Literal

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
        num_with_sources=0
        sum_sources=0
        
        countries=[]
        num_languages=[]

        num_incidents=len(self.incidents)
        for incident in self.incidents:
            for ref_text in incident.reference_texts:
                if ref_text.wiki_content:
                    num_with_wikipedia+=1
                if len(ref_text.sources):
                    num_with_sources+=1
                    sum_sources+=len(ref_text.sources)
            if len(incident.reference_texts)==3:
                print(incident.wdt_id)
            num_languages.append(len(incident.reference_texts))
            countries.append(incident.country_name)
        if num_with_sources: 
            avg_sources=sum_sources/num_with_sources
        else:
            avg_sources=0
        countries_dist=Counter(countries)
        numlang_dist=Counter(num_languages)
        
        return num_incidents, num_with_wikipedia, num_with_sources, avg_sources, countries_dist, numlang_dist
    
    def serialize(self, filename=None):
        """
        Serialize a collection of incidents to a .ttl file.
        """
        
        g = Graph()
        
        # Namespaces definition
        SEM=Namespace('http://semanticweb.cs.vu.nl/2009/11/sem/')
        WDT_ONT=Namespace('http://www.wikidata.org/wiki/')
        GRASP=Namespace('http://groundedannotationframework.org/grasp#')
        g.bind('sem', SEM)
        g.bind('wdt', WDT_ONT)
        g.bind('grasp', GRASP)

        # Some core URIs/Literals
        election=URIRef('https://www.wikidata.org/wiki/Q40231')
        election_label=Literal('election')
        country_label=Literal('country')
        
        for incident in self.incidents:
            event_id = URIRef(incident.wdt_id)

            # event labels in all languages
            for ref_text in incident.reference_texts:
                name_in_lang=Literal(ref_text.name, lang=ref_text.language)
                g.add(( event_id, RDFS.label, name_in_lang))

                # denotation of the event
                wikipedia_article=URIRef(ref_text.wiki_uri)
                g.add(( event_id, GRASPdenotedIn, wikipedia_article ))

            # event type information
            g.add( (event_id, RDF.type, SEM.Event) )
            g.add(( event_id, SEM.eventType, election))

            # time information
            timestamp=Literal(incident.time)
            g.add((event_id, SEM.hasTimeStamp, timestamp))

            # place information
            country=URIRef(incident.country_id)
            country_name=Literal(incident.country_name)
            g.add((event_id, SEM.hasPlace, country))
            g.add((country, RDFS.label, country_name))
            g.add((country, RDF.type, WDT_ONT.Q6256))

        g.add((election, RDFS.label, election_label))
        g.add((election, RDFS.label, country_label))

        # Done. Store the resulting .ttl file now...
        if filename: # if a filename was supplied, store it there
            g.serialize(format='turtle', destination=filename)
        else: # else print to the console
            print(g.serialize(format='turtle'))

class Incident:

    def __init__(self, 
                incident_type,
                wdt_id,
                country_id,
                country_name,
                time,
                english_name,
                reference_texts=[]):
        self.incident_type=incident_type
        self.wdt_id=wdt_id
        self.country_id=country_id
        self.country_name=country_name
        self.time=time
        self.english_name=english_name
        self.reference_texts=reference_texts
        
        
class ReferenceText:
    
    def __init__(self,
                wiki_uri='',
                name='',
                wiki_content='',
                language='',
                sources=''):
        self.name=name
        self.wiki_uri=wiki_uri
        self.wiki_content=wiki_content
        self.language=language
        self.sources=sources

