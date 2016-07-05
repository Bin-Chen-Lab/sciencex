'''
Created on Jan 10, 2014

@author: binchen1
'''
from dbconnector import dbconnector
import re

def getCompanyConcepts(company):
        output = []
        db = dbconnector().getNewCon()
        cur = db.cursor() 
        cur.execute("select concept, sum(relevance) as score, count(*)  from gscholar_concept a join gscholar b on a.gscholar_id = b.id where company = '%s' and relevance > 0.9 and type = 'keyword'  group by concept having count(*)>1 order by score desc limit 20" % company)
        for (concept, score, count) in cur :
            if not __isNoisy__(concept, company):
                output.append({"concept" : concept, "score" : score, "count" : count})
        cur.close()
        db.close()
        
        return output

def getCompanies():
        output = []
        db = dbconnector().getNewCon()
        cur = db.cursor() 
        cur.execute("select company, sum(citations) as HIndex , count(*) as publications from  gscholar where pmid != 'None' and pmid !='0' group by company order by HIndex desc limit 50")
        for (company, HIndex, publications) in cur :
                concepts = getCompanyConcepts(company)
                output.append({"company" : company, "HIndex" : HIndex, "publications" : publications, "concepts" : concepts})
        cur.close()
        db.close()
        
        return output

def getCompanyNames():
        output = []
        db = dbconnector().getNewCon()
        cur = db.cursor() 
        cur.execute("select  name from company")
        for (name) in cur :
                output.append(str(name))
        cur.close()
        db.close()
        
        return output
                
def __isNoisy__(concept, company):
    concept = concept.upper()
    company = company.upper()
    if concept.find(company) > -1:
        return True
    
    stopWords = ['Inc.', 'Corp', 'www', 'USA']
    for word in stopWords:
        if concept.find(word) > -1:
            return True
        
  
#print(getConcepts(""))
#print(getCompanyNames())