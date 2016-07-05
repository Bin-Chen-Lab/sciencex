'''
Created on Jan 4, 2015

@author: binchen1
'''

import re

if __name__ == '__main__':
    pass

synonyms = {
            "anti": "(anti- OR antibody)",
            "antibody": "(anti- OR antibody)",
            "immunohistochemistry": "(Immunohistochemistry OR IHC)",
            "ihc": "(Immunohistochemistry OR IHC)", 
            "immunocytochemistry": "(Immunocytochemistry OR ICC)",
            "icc": "(Immunocytochemistry OR ICC)"                         
            }

def replaceSynonyms(query):
    groups = []
    #if quoted, do not change it
    if query.startswith('"') and query.endswith('"'):
        #print  re.match(r'".*"', query).group(0)
        return query
    
    for m in re.finditer(r"[\w']+|[.,!?;]", query):
        if (m.group(0).lower() in synonyms):
            groups.append(synonyms[m.group(0).lower()])
        else:
            groups.append(m.group(0))
    return " ".join(groups)

print replaceSynonyms('Actin Gamma 2 Antibody')