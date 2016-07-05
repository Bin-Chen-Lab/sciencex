'''
Created on Dec 31, 2013

@author: binchen1
'''
import os, os.path
import codecs
import datetime
import random
from operator import itemgetter, attrgetter
from collections import Counter


from whoosh.index import create_in
from whoosh.index import open_dir
from whoosh import index
from whoosh import writing, highlight
from whoosh.qparser import QueryParser
from whoosh.qparser import MultifieldParser
from whoosh.fields import *

from dbconnector import dbconnector
from django.conf import settings
from pubmed.pubmed import pubmed_utilities

import synonyms


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
        keyword = synonyms.replaceSynonyms(keyword)
        print keyword
        output = []
        #print self.getSchema()
        with self.ix.searcher() as searcher:
            query = MultifieldParser(["content", "article_title", "authors"], self.getSchema()).parse(keyword)
            #query = QueryParser(["content","aritlce_title"], self.getSchema()).parse(keyword)
            results = searcher.search(query, limit = self.MAX_RESULTS)
            results.fragmenter = highlight.WholeFragmenter()
            
            print results.estimated_length()
            
            rank = 0
            for hit in results:
                rank = rank + 1
                #for some entries with NULL if_score, its value was changed
                if (hit["if_score"] > 10000 or hit["if_score"] < 0):
                    score = 0
                else:
                    score = hit["if_score"]
                
                #title and authors should appear any time, only the content matched will return.    
                output.append({"title" : hit["title"],  "content" : hit.highlights("content") if len(hit.highlights("content")) > 0 else hit["company_name"],
                               "article_title" : hit.highlights("article_title") if len(hit.highlights("article_title")) >0 else hit['article_title'] ,
                                "authors" : hit.highlights("authors") if len(hit.highlights("authors")) > 0 else hit['authors'], 
                                "rank_relevance": rank, "year": hit["year"], "if_score": score, "company": hit["company"], "journal": hit["journal"], "pmcid": hit["pmcid"], "pmid": hit["pmid"]})
                #"content" : hit.highlights("content"),
        return output
    
    def rankResults(self, results):
        
        #rank score = rank by relevance + rank by importance / 2
        results = sorted(results, key= itemgetter("if_score"), reverse=True )
        count = 0
        for result in results:
            count = count + 1
            result['rank_importance'] = count
            result['score'] = (count + result['rank_relevance']) / 2.0
            result['reverse_score'] = 1.000/result['score']
        #rank 
        return results
    
    def scoreCompany(self, results):
        companyScore =  {}
        for result in results:
            if result['company'] in companyScore:
                companyScore[result['company']] = companyScore[result['company']] + result['reverse_score']
            else:
                companyScore[result['company']] = result['reverse_score']
        

        return companyScore       
            
    
    def getPublicationInfo(self, results):
        ids = []
        gscholarinfo = {}
        outputinfo = []
        
        #get ids
        for result in results:
            ids.append((result["title"].replace("","")))

        if len(ids) == 0:
            return outputinfo
        
        #retrieve publication info
        db = dbconnector().getNewCon()
        cur = db.cursor() 
        query = ("SELECT id, company, pmid, journal, IF_score, year, pmc, comp_id, title, authors  FROM publications  where  id in (" + ','.join(ids) + ") order by IF_score desc")

        cur.execute(query)

        pubmed = pubmed_utilities()
        
        for (id, company,  pmid, journal, IF_score, year, pmc , comp_id, title, authors ) in cur :
            #some publication, the title and authors are not uploaded, so retrieve from the API
            if title:                
                try:
                    paper_meta = pubmed.get_paper_meta_summary(pmid)[0]['summary']
                except:
                    paper_meta = "\t\t\t\t"
                
                title = paper_meta.split("\t")[1]
                authors = paper_meta.split("\t")[0]
                
            gscholarinfo[str(id)] = {"company_name" : company,   "pmid" : pmid
                      , "journal" : journal, "citations" : IF_score, "year" : year, "pmcid" : pmc, "company": comp_id, "authors": authors, "title": title }
                       
        for result in results:
            gscholar = gscholarinfo[str(result["title"])]
            gscholar['content_parsed'] = result["content"]
            gscholar['score'] = result['score']
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
    
    def getCompanyInfo2(self, results, pub_per_comp= 1000):
        ids = []
        outputinfo = []
        
        #get ids
        for result in results:
            ids.append((result["title"].replace(": ","")))

        if len(ids) == 0:
            return outputinfo
        
        #retrieve publication info
        publications = self.getPublicationInfo(results)

        #group company and rank company
        companyScore = self.scoreCompany(results)
        
        #retrieve  info
        db = dbconnector().getNewCon()
        cur = db.cursor() 
        query = ("SELECT name, url, comp_id  FROM companies where  comp_id in (" + ','.join(map(str, companyScore.keys())) + ")")
        cur.execute(query)
        
        
        #get all companies
        companies = self.__getCompanyNames__()
        
        for (name, url, comp_id ) in cur :
            companyScholars = []
            for publication in publications:
                if publication["company"] == comp_id: # and self.__isKeywordMatchCompany__(publication["company_name"], companies, publication["content_parsed"]):
                    companyScholars.append(publication)
            
            companyScholars = sorted(companyScholars, key= itemgetter("score"), reverse=True )
            
            hits = len(companyScholars) 
            if hits > pub_per_comp:
                companyScholars = companyScholars[0:pub_per_comp]
                
                
            if hits > 0:        
                outputinfo.append({"company": comp_id, "company_name": name, "score": companyScore[comp_id], "hits" : hits, "url": url,   "publication": companyScholars}) #
            
        cur.close()
        db.close()
        
        outputinfo = sorted(outputinfo, key= itemgetter("score"), reverse=True)
        
        return outputinfo
    
    def getCompanyInfo(self, results, pub_per_comp= 1000):
        ids = []
        outputinfo = []
        
        #get ids
        for result in results:
            ids.append((result["title"].replace(": ","")))

        if len(ids) == 0:
            return outputinfo
        
        #group company and rank company
        companyScore = self.scoreCompany(results)
        #only show results for top 10 company
        companyScore = dict(sorted(companyScore.items(), key=lambda x: x[1],reverse=True)[:9]) #Counter(companyScore).most_common(10) #sorted(companyScore.iteritems(), key= itemgetter(1), reverse=True )
        #print companyScore
       # print results
       # print companyScore
        
        #retrieve  info
        db = dbconnector().getNewCon()
        cur = db.cursor() 
        query = ("SELECT name, url, comp_id  FROM companies where  comp_id in (" + ','.join(map(str, companyScore.keys())) + ")")
        cur.execute(query)
         
        for (name, url, comp_id ) in cur:
            companyScholars = []
            for result in results:
                if result['company'] == comp_id:
                    companyScholars.append(result)
                    #print result
            companyScholars = sorted(companyScholars, key= itemgetter("reverse_score"), reverse=True )
            
            hits = len(companyScholars) 
            if hits > pub_per_comp:
                companyScholars = companyScholars[0:pub_per_comp]
                
                
            if hits > 0:        
                outputinfo.append({"company": comp_id, "company_name": name, "score": companyScore[comp_id], "hits" : hits, "url": url,   "publication": companyScholars}) #
            
        cur.close()
        db.close()
        
        outputinfo = sorted(outputinfo, key= itemgetter("score"), reverse=True)
        
        return outputinfo
        
    
    def getCompanyInfo1(self, results):
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
                outputinfo.append({"company": company, "hits" : hits, "url": url, "search_url": search_url,  "gscholar": companyScholars}) #
            
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
        return Schema(title=TEXT(stored=True), path=ID(stored=True), company_name=TEXT(stored=True), content=TEXT(stored=True), article_title=TEXT(stored=True), authors=TEXT(stored=True), 
                      journal=TEXT(stored=True), year = NUMERIC(stored=True, sortable=True), pmcid = NUMERIC(stored=True), pmid = NUMERIC(stored=True), if_score = NUMERIC(stored=True, sortable=True), company = NUMERIC(stored=True))
   
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
        return Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT(stored=True), article_title=TEXT(stored=True), authors=TEXT(stored=True), year = NUMERIC(stored=True, sortable=True), if_score = NUMERIC(stored=True, sortable=True), company = NUMERIC(stored=True))


#test_index = indexer("../../data/indexer/companydb")
#test_index.clearIndexer
#test_index.loadByDb()
def storeQuery(query):
    db = dbconnector().getNewCon()
    cur = db.cursor() 
    insert_query = ("insert into user_queries(query, query_date) values(%s, %s)")
    data_query = (query.encode('utf-8'), datetime.datetime.now())
    cur.execute(insert_query, data_query)
    cur.close()
    db.commit()
    db.close()
    
def fulltext_search(query):
    storeQuery(query)
    test_searcher = searcher(settings.FULLTEXT_DIR)
    results = test_searcher.searchByKeyword(query) 
    results = test_searcher.rankResults(results)
    return (len(results), test_searcher.getCompanyInfo(results, 2))

def fulltext_search_filter_by_company(query, company, maximum=30):
    #print settings.FULLTEXT_DIR
    test_searcher = searcher(settings.FULLTEXT_DIR)
    results = test_searcher.searchByKeyword(query)
    results = test_searcher.rankResults(results)
    company_results = []
    for result in results:
        if str(result['company']) == company:
            company_results.append(result)
            if len(company_results) > maximum:
                break
    return ('', test_searcher.getCompanyInfo(company_results))

#print searchByKeyword("ap1")
#print fulltext_search("antibody")
#print fulltext_search_filter_by_company("antibody", 670L)