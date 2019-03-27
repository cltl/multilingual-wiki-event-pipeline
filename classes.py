from collections import Counter

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
            num_languages.append(len(incident.reference_texts))
            countries.append(incident.country_name)
        
        avg_sources=sum_sources/num_with_sources
        countries_dist=Counter(countries)
        numlang_dist=Counter(num_languages)
        
        return num_incidents, num_with_wikipedia, num_with_sources, avg_sources, countries_dist, numlang_dist

class Incident:

    def __init__(self, 
                incident_type,
                wdt_id,
                country_id,
                country_name,
                time,
                reference_texts=[]):
        self.incident_type=incident_type
        self.wdt_id=wdt_id
        self.country_id=country_id
        self.country_name=country_name
        self.time=time
        self.reference_texts=reference_texts
        
        
class ReferenceText:
    
    def __init__(self,
                name='',
                wiki_content='',
                language='',
                sources=''):
        self.name=name
        self.wiki_content=wiki_content
        self.language=language
        self.sources=sources

