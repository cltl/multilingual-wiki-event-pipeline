import pickle
import utils
import pandas
import networkx as nx


def combine_freq_and_ontological_information(path_directed_graph,
                                             path_event2freq,
                                             output_path,
                                             verbose=0):
    g = nx.read_gpickle(path_directed_graph)
    event2instance_frequency = pickle.load(open(path_event2freq, 'rb'))


    list_of_lists = []
    headers = ['event_url', 'shortest_path_to_event',
               'shortest_path_length',
               'number_of_descendants',
               'freq', 'freq_with_ancestors']

    event_node = 'wd:Q1656682'
    all_event_subclasses = nx.descendants(g, 'wd:Q1656682')
    for event_type in all_event_subclasses:

        event_url = event_type.replace('wd:', 'http://www.wikidata.org/entity/')
        shortest_path = nx.shortest_path(g, event_node, event_type)

        freq = event2instance_frequency.get(event_type, 0)
        the_descendants = nx.descendants(g, event_type)
        total_freq = sum([event2instance_frequency.get(an_event_type, 0)
                          for an_event_type in the_descendants])


        one_row = [event_url,
                   shortest_path, len(shortest_path),
                   len(the_descendants),
                   freq, total_freq]
        list_of_lists.append(one_row)

    df = pandas.DataFrame(list_of_lists, columns=headers)

    df.to_excel(output_path)

def chosen_events_in_latex(excel_path, chosen_event_types):

    df = pandas.read_excel(excel_path)
    list_of_lists = []
    headers = ['event type', 'length of path to event node', '# of descendants', 'cumulative frequency']
    for index, row in df.iterrows():
        event_url = row['event_url']
        if event_url in chosen_event_types:
            event_type = chosen_event_types[event_url]
            one_row = [
                event_type,
                row['shortest_path_length'],
                row['number_of_descendants'],
                row['freq_with_ancestors']
            ]
            list_of_lists.append(one_row)

    df = pandas.DataFrame(list_of_lists, columns=headers)
    return df.to_latex(index=False)

utils.extract_subclass_of_ontology(utils.wdt_sparql_url, 'ontology', 'relations.p', verbose=2)

g = utils.load_ontology_as_directed_graph('ontology/relations.p', 'ontology/g.p', verbose=2)

event2instance_frequency = utils.load_event_type2instancefreq(utils.wdt_sparql_url, 'ontology/event2instance_freq.p', verbose=2)

combine_freq_and_ontological_information('ontology/g.p',
                                         'ontology/event2instance_freq.p',
                                         'ontology/overview.xlsx')

chosen_event_types = {'http://www.wikidata.org/entity/Q500834': 'tournament',
                      'http://www.wikidata.org/entity/Q189760': 'voting',
                      'http://www.wikidata.org/entity/Q327197': 'legal transaction',
                      'http://www.wikidata.org/entity/Q22938576': 'race',
                      'http://www.wikidata.org/entity/Q2627975': 'ceremony'}

latex = chosen_events_in_latex('ontology/overview.xlsx', chosen_event_types)
print(latex)
