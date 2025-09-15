import re
from operator import itemgetter


def generate_key_word_dict(d):
    result = {}
    for name in d:
        res_list = re.findall('[A-Z][^A-Z]*', name)
        res_list.append(name)
        for item in res_list:
            item = str(item).lower()
            if item not in result:
                result[item] = []
            result[item].append((name, len(item) / len(name)))
    for key in result:
        result[key] = sorted(result[key], key=itemgetter(1), reverse=True)
    return result


def find_key_word(kw, d, raw_keys=[]):
    kw = str(kw).lower()
    if kw in d:
        result = d[kw]
    else:
        match_keys = re.findall('[a-z]*', kw)

        if len(match_keys) > 1:
            temp_result = {}
            for item in raw_keys:
                temp_result[item] = {
                    "key": item,
                    "lower": item.lower(),
                    "count": 0
                }
            for match_key in match_keys:
                for raw_key in raw_keys:
                    if raw_key.lower().find(match_key) >= 0:
                        temp_result[raw_key]["count"] = temp_result[raw_key]["count"] + 1
            result = []
            for key in temp_result:
                val = temp_result[key]
                if val["count"] == len(match_keys):
                    result.append((key, len(kw) / len(key)))
            result = sorted(result, key=itemgetter(1), reverse=True)
        else:
            match_kw = None
            factor = 0
            for key in d:
                if key.find(kw) >= 0:
                    temp_factor = len(kw) / len(key)
                    if temp_factor > factor:
                        match_kw = key
                        factor = temp_factor
            if match_kw is not None:
                result = d[match_kw]
            else:
                result = []
        # result = process.extract(kw, raw_keys, limit=5)
        # print("extract:",result)
    r = [item[0] for item in result]
    # print("find_key_word:", kw, r)
    # if len(r) > 5:
    #     r = r[:10]
    return r
