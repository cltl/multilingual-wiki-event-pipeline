
def mapping_wid2tid(doc):
    """
    create mapping from w_id to t_id

    :param lxml.etree._ElementTree doc: XML document loaded by lxml.etree

    :rtype: dict
    :return: w_id -> t_id

    :raises: Exception when a w_id maps to more than one t_id
    :raises: Exception when a t_id maps to more than one w_id
    """
    wid2tid = {}

    for term_el in doc.xpath('terms/term'):
        t_id = term_el.get('id')

        target_els = term_el.findall('span/target')
        assert len(target_els) == 1, f'expecting one target el per term, found {len(target_els)}'

        for target_el in term_el.xpath('span/target'):
            w_id = target_el.get('id')

            if w_id in wid2tid:
                raise Exception(f'{w_id} maps to two or more t_ids')
            else:
                wid2tid[w_id] = t_id

    return wid2tid