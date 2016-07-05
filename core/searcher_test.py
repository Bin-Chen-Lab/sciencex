'''
Created on Dec 31, 2013

@author: binchen1
'''
import os, os.path

from whoosh.index import create_in
from whoosh.index import open_dir
from whoosh import index
from whoosh import writing, highlight
from whoosh.qparser import QueryParser

from whoosh.fields import *

import codecs
from dbconnector import dbconnector

from django.conf import settings

import datetime

from operator import itemgetter, attrgetter

import random

from whoosh.analysis import StemmingAnalyzer
'''
index coded in pysciencex
class indexer(object):



    def __init__(self, indexdir):

        schema = self.getSchema()
        if index.exists_in(indexdir):
        #if exist, open it; otherwise, create one
            self.ix = index.open_dir(indexdir)
        else:
            if not os.path.exists(indexdir):
                os.mkdir(indexdir)
            self.ix = index.create_in(indexdir, schema)

    def _getFiles_(self, dir):
    #read files
        import os 
        #os.chdir(self.dir)
        filelist = [ f for f in os.listdir(dir) if f.endswith(".txt") ]
        return (filelist)

    def loadByFolder(self, datadir):
        files = self._getFiles_(datadir)
        print files
        writer = self.ix.writer()
        
        for file in files:
            with  codecs.open(datadir + "/"+ file,"r", "utf-8") as f:
                line_number = 0
                for line in f:
                    line_number += 1
                    writer.add_document(title= (file + "_" + str(line_number)).decode('utf-8') , path=u"/a",
                                        content= (line.strip())) 
        writer.commit()
 
    def loadByDb(self, company=''):
        writer = self.ix.writer()

        db = dbconnector().getNewCon()
        cur = db.cursor() 
        if company == '':
            cur.execute("SELECT id, company, title, authors, content_parsed FROM gscholar where content_parsed is not null and pmid != '0' and pmid !='None'")
        else:
            cur.execute("SELECT id, company, title, authors, content_parsed FROM gscholar where content_parsed is not null and pmid != '0' and pmid !='None' and company='%s'" % company)

        for (id, company, title, authors, content_parsed) in cur :
            print "working on row " + str(id)
            writer.add_document(title= str(id).decode() , path=u"/a",
                                        content= company.decode("utf-8") + ";" + title.decode("utf-8")  + ";" +  authors.decode("utf-8")  + ";" +  content_parsed.decode("utf-8")) 
        writer.commit()
        cur.close()
        db.close()
                           
    def loadByFile(self, file):
        pass
    
    def clearIndexer(self):
        mywriter = self.ix.writer()
        mywriter.commit(mergetype=writing.CLEAR)
    
    def getSchema(self):
        return Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT(stored=True))
'''
  
class searcher(object):
    '''
    classdocs
    '''
    MAX_RESULTS = 500

    def __init__(self, indexdir):
        '''
        Constructor
        '''
        
        if index.exists_in(indexdir):
        #if exist, open it; otherwise, create one
            self.ix = index.open_dir(indexdir)
        else:
            print (indexdir + " does not exist, creating a new one....")
            if not os.path.exists(indexdir):
                os.mkdir(indexdir)
            self.ix = index.create_in(indexdir, self.getSchema())
            
    
    def searchByKeyword(self, keyword):
        output = []

        with self.ix.searcher() as searcher:
            query = QueryParser("content", self.getSchema()).parse(keyword)
            results = searcher.search(query, limit = self.MAX_RESULTS)
            results.fragmenter = highlight.WholeFragmenter()
            
            
            print results.estimated_length()
            
            rank = 0
            for hit in results:
                rank = rank + 1
                output.append({"title" : hit["title"], "content" : hit.highlights("content")}, "rank", rank)
                
                #print hit.highlights("content")

    
        return output
    
    def getPublicationInfo(self, results):
        ids = []
        contents = []
        gscholarinfo = {}
        outputinfo = []
        
        #get ids
        for result in results:
            ids.append((result["title"].replace("","")))
            contents.append((result["content"].replace("","")))

        if len(ids) == 0:
            return outputinfo
        
        #retrieve publication info
        db = dbconnector().getNewCon()
        cur = db.cursor() 
        query = ("SELECT id, company, pmid, journal, IF_score, year, pmc  FROM publications  where  id in (" + ','.join(ids) + ") order by IF_score desc")

        cur.execute(query)

        for (id, company,  pmid, journal, IF_score, year, pmc  ) in cur :
            gscholarinfo[str(id)] = {"company" : company,   "pmid" : pmid
                      , "journal" : journal, "citations" : IF_score, "year" : year, "pmcid" : pmc}
            
            
        for result in results:
            gscholar = gscholarinfo[str(result["title"])]
            gscholar['content_parsed'] = result["content"]
            outputinfo.append(gscholar)
            
        cur.close()
        db.close()
        return outputinfo
           
    def getGscholarInfo(self, results):
        ids = []
        contents = []
        gscholarinfo = {}
        outputinfo = []
        
        #get ids
        for result in results:
            ids.append((result["title"].replace("","")))
            contents.append((result["content"].replace("","")))

        if len(ids) == 0:
            return outputinfo
        
        #retrieve gsholar info
        db = dbconnector().getNewCon()
        cur = db.cursor() 
        query = ("SELECT id, company, title, authors, content_parsed, pmid, journal, citations, year, pmcid FROM gscholar  where  id in (" + ','.join(ids) + ") order by citations desc")

        cur.execute(query)

        for (id, company, title, authors, content_parsed, pmid, journal, citations, year, pmcid ) in cur :
            gscholarinfo[str(id)] = {"company" : company,  "title" : title , "authors" :  authors , "content_parsed1" :  content_parsed, "pmid" : pmid
                      , "journal" : journal, "citations" : citations, "year" : year, "pmcid" : pmcid}
            
            
        for result in results:
            gscholar = gscholarinfo[str(result["title"])]
            gscholar['content_parsed'] = result["content"]
            outputinfo.append(gscholar)
            
        cur.close()
        db.close()
        return outputinfo
 
    def getCompanyInfo(self, results):
        ids = []
        outputinfo = []
        

        #get ids
        for result in results:
            ids.append((result["title"].replace(": ","")))

        if len(ids) == 0:
            return outputinfo
        
        #retrieve  info
        db = dbconnector().getNewCon()
        cur = db.cursor() 
        query = ("SELECT company, b.url, b.search_url, count(*) as hits FROM publications a join company b on a.company=b.name where  id in (" + ','.join(ids) + ") group by company, b.url order by hits desc")

        cur.execute(query)
        
        #gscholars = self.getGscholarInfo(results)
        gscholars = self.getPublicationInfo(results)
        
        #get companies
        companies = self.__getCompanyNames__()
        
        for (company, url, search_url, hits ) in cur :
            companyScholars = []
            for gscholar in gscholars:
                if gscholar["company"] == company and self.__isKeywordMatchCompany__(company, companies, gscholar["content_parsed"]):
                    companyScholars.append(gscholar)
            
            companyScholars = sorted(companyScholars, key= itemgetter("citations"), reverse=True )
            
            hits = len(companyScholars) 
            if hits > 2:
                companyScholars = companyScholars[0:2]
                
                
            if hits > 0:        
                outputinfo.append({"company": company, "hits" : hits, "url": url, "search_url": search_url, "price": self.getPrice(), "availability": self.getAvailability(), "gscholar": companyScholars}) #
            
        cur.close()
        db.close()
        
        outputinfo = sorted(outputinfo, key= itemgetter("hits"), reverse=True)
        
        return outputinfo
       
    def getPrice(self):
        return random.randint(150, 400)
        
    def getAvailability(self):
        foo = ["in stock", "1 day", "2 days"]
        from random import choice
        return choice(foo)
    
    def getSchema(self):
        return Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT(stored=True))

    def __isKeywordMatchCompany__(self,  company, companies, sentence):
        #check if keyword is really related to the target company; the assumption is that between the keyword and company, there is no suspicious company
        sentence = re.sub(' +',' ', sentence) #remove multiple spaces in a sentence
        company = company.split(" ")[0] #look at the first word; #need comeback to deal with the multiple words
        valid = re.compile(r'%s.*%s' % ('<b class="match term0"', company), re.IGNORECASE)
        match_groups = valid.findall(sentence)
        
        if len(match_groups) <= 0:
            #print "company %s not in %s" % (company.encode("utf8"), sentence.encode("utf8"))            
            return False
        
        wordsBetweenHitsCompany = match_groups[0]
        wordsBetweenHitsCompany = wordsBetweenHitsCompany.replace( company, '')
        
       # specialWords = ['Inc.', 'Corp', 'LLC.', 'Corporation', 'Labs', 'Biotechnology', 'Laboratories', 'International', 'Company', 'Ltd.', 'Laboratory', 'Limited', ]
        specialWords = ['Company', 'Biotechnology', 'International', 'Laboratory', 'limited', 'ltd.', 'ltd', 'pvt ltd', 'pvt.ltd.', 'pvt ltd.', 'incorporation', 'inc.', 'inc', 'incorporated', 'corp', 'corporation', 'corp.', 'co.' , 'co.', 'llc', 'llc.','s.r.l.', 'srl','laboratories','labs', 'sa', 's.a', 'sl', 's.l', 's.l.', 'bv', 'b.v.', 'gmbh', 'ag', 'a/s', 's.p.a.']

        for company in specialWords:
            if wordsBetweenHitsCompany.find(company) > -1:
                return False
            
        for company in companies:
            if wordsBetweenHitsCompany.find(company) > -1:
                return False
        
        return True
    
    def __getCompanyNames__(self):
        import company
        companies = company.getCompanyNames()
        return companies
    
class schema(object):
    '''
    classdocs
    '''


    def __init__(self, indexdir):    
        pass
           
    def getSchema(self):
        return Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT(stored=True, analyzer=StemmingAnalyzer()))


#test_index = indexer("../../data/indexer/companydb")
#test_index.clearIndexer
#test_index.loadByDb()
def storeQuery(query):
    db = dbconnector().getNewCon()
    cur = db.cursor() 
    insert_query = ("insert into user_queries(query, query_date) values(%s, %s)")
    data_query = (query, datetime.datetime.now())
    cur.execute(insert_query, data_query)
    cur.close()
    db.commit()
    db.close()
    
def fulltext_search(query):
    storeQuery(query)
    test_searcher = searcher(settings.FULLTEXT_DIR)
    results = test_searcher.searchByKeyword(query)
    return ('', test_searcher.getCompanyInfo(results))

from whoosh.qparser import QueryParser
from whoosh.query import Variations, FuzzyTerm

parser = QueryParser("content", schema=schema(settings.FULLTEXT_DIR).getSchema(), termclass=Variations)
print parser.parse(u"render")


from whoosh import qparser

# Parse the user query string
schema(settings.FULLTEXT_DIR).getSchema()
qstring = 'looking renders'
qp = qparser.QueryParser("content", schema(settings.FULLTEXT_DIR).getSchema(), termclass=Variations)
#qp.add_plugin(qparser.FuzzyTermPlugin())
q = qp.parse(qstring)
print q


ix = index.open_dir(settings.FULLTEXT_DIR)

with ix.searcher() as s:
    corrected = s.correct_query(q, qstring)
    print corrected.string
    if corrected.query != q:
        print("Did you mean:", corrected.string)

        
#print fulltext_search("ELISA")[1]