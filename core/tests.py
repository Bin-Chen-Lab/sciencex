from django.test import TestCase

from core.models import gscholar
import company
from searcher import searcher
import re

companies= company.getCompanyNames(
                        )
sentence = 'anti-<b class="match term0">EGFR</b> Corporation ( Cell   Signaling   echnology ) '


def isKeywordMatchCompany(  company, companies, sentence):
    #check if keyword is really related to the target company; the assumption is that between the keyword and company, there is no suspicious company
    valid = re.compile(r'%s.*%s' % ('<b class="match term0"', company), re.IGNORECASE)
    match_groups = valid.findall(sentence)
    
    if len(match_groups) <= 0:
        #print "company %s not in %s" % (company, sentence)
        return False
    
    wordsBetweenHitsCompany = match_groups[0]
    wordsBetweenHitsCompany = wordsBetweenHitsCompany.replace( company, '')
    
    print wordsBetweenHitsCompany
    specialWords = ['Inc.', 'Corp', 'LLC.', 'Corporation', 'Labs', 'Biotechnology', 'Laboratories', 'International', 'Company', 'Ltd.', 'Laboratory', 'Limited']
    for company in specialWords:
        if wordsBetweenHitsCompany.find(company) > -1:
            return False
        
    for company in companies:
        if wordsBetweenHitsCompany.find(company) > -1:
            return False
    
    return True

print isKeywordMatchCompany("Cell  Signaling   Technology", companies, sentence)

# Create your tests here.
#paper = gscholar.objects.get(pk=1)
#print paper