'''
Created on Jan 10, 2014

@author: binchen1
'''
from dbconnector import dbconnector
import re

def getConcepts():
        output = []
        db = dbconnector().getNewCon()
        cur = db.cursor() 
        cur.execute("select concept, sum(relevance) as score, count(*) as count from gscholar_concept a join gscholar b on a.gscholar_id = b.id where  relevance > 0.9 and type = 'keyword'  group by concept having count(*)>1 order by count desc limit 200" )
        for (concept, score, count) in cur :
            if  __concept__(concept):
                output.append({"concept" : concept, "score" : score, "count" : count})
        cur.close()
        db.close()
        
        return output
    
def __concept__(concept):
   
    hints = ['assay', 'screen', 'antibody', 'chemical', 'sequence']
    for hint in hints:
        if concept.find(hint) > -1:
            return True
    return False
        
    
#print(getConcepts())