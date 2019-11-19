import json
from collections import defaultdict

def create_indices_from_bin(inc_data, project, json_dir):

    inc2doc_file='%s/inc2doc_index.json' % json_dir
    inc2str_file='%s/inc2str_index.json' % json_dir
    proj2inc_file='%s/proj2inc_index.json' % json_dir
    type2inc_file='%s/type2inc_index.json' % json_dir

    inc2doc={}
    inc2str={}
    proj2inc=defaultdict(set)
    type2inc=defaultdict(set)

    for inc in inc_data.incidents:
        str_data={}
        for k, v in inc.extra_info.items():
            str_data[k]=list(v)
            
        rts=[]
        for rt in inc.reference_texts:
            rt_info='%s/%s' % (rt.language, rt.name)
            rts.append(rt_info)
        key=inc.wdt_id
        inc2doc[key]=rts
        inc2str[key]=str_data
        proj2inc[project].add(key)
        type2inc[inc.incident_type].add(key)


    new_t2i={}
    for k,v in type2inc.items():
        new_t2i[k]=sorted(list(v))
    new_p2i={}
    for k,v in proj2inc.items():
        new_p2i[k]=sorted(list(v))

    with open(inc2doc_file, 'w') as f:
        json.dump(inc2doc, f)
    with open(inc2str_file, 'w') as f:
        json.dump(inc2str, f)
    with open(proj2inc_file, 'w') as f:
        json.dump(new_p2i, f)
    with open(type2inc_file, 'w') as f:
        json.dump(new_t2i, f)
