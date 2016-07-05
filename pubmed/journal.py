'''
This  class is to model journal
Created Apr 2013
@author: Bin Chen
'''
import csv

class journal:
        def __init__(self):            
                fname = "data/journal_impact_factor_2012.csv"
                self.journal_IF = {}
                for row in csv.DictReader(open(fname, 'rU'), delimiter=','):
                        self.journal_IF[row.get('ISSN')] = row.get('Impact Factor')
                    
        def get_journal_IF(self,issn):
                if issn in self.journal_IF:
                        return self.journal_IF[issn]
                else:
                        return 0
        

#j = journal()
#print(j.get_journal_IF('0028-4793o'))


