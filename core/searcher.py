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
from itertools import groupby

from whoosh.index import create_in
from whoosh.index import open_dir
from whoosh import index
from whoosh import writing, highlight
from whoosh.qparser import QueryParser
from whoosh.qparser import MultifieldParser
from whoosh.fields import *
from whoosh import scoring

from dbconnector import dbconnector
from django.conf import settings
from pubmed.pubmed import pubmed_utilities

import synonyms


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
             
            query = MultifieldParser(["content", "article_title", "authors", "context"], self.getSchema()).parse(keyword)
            #query = QueryParser(["content","aritlce_title"], self.getSchema()).parse(keyword)
            results = searcher.search(query, limit = self.MAX_RESULTS)
            results.fragmenter = highlight.WholeFragmenter()
            
            print results.estimated_length()
            #print scoring.BM25F().scorer(searcher, "content", keyword).score(query.matcher(searcher))

            rank = 0
            for hit in results:
                rank = rank + 1
                if rank == 1:
                    best_score = hit.score
                #for some entries with NULL if_score, its value was changed
                if (hit["if_score"] > 10000 or hit["if_score"] < 0):
                    score = 0
                else:
                    score = hit["if_score"]
                
                #title and authors should appear any time, only the content matched will return.    
                output.append({"source": hit["source"], "title" : hit["title"],  "content" : hit.highlights("content") if len(hit.highlights("content")) > 0 else hit["company_name"],
                               "article_title" : hit.highlights("article_title") if len(hit.highlights("article_title")) >0 else hit['article_title'] ,
                                "authors" : hit.highlights("authors") if len(hit.highlights("authors")) > 0 else hit['authors'], 
                                "concepts": hit['concept'], "context":  hit.highlights("context") if len(hit.highlights("context")) > 0 else hit['context'], 
                                "rank_relevance": hit.score/best_score, "year": hit["year"], "if_score": score, "company": hit["company"], 
                                "journal": hit["journal"], "sourceid": hit["sourceid"], "pmid": hit["pmid"],  })
                #"content" : hit.highlights("content"),
        return output
    
    def rankResults(self, results):
        
        #rank score = rank by relevance + rank by importance / 2
        results = sorted(results, key= itemgetter("if_score"), reverse=True )
        count = 0
        for result in results:
            count = count + 1
            if count == 1:
                best_if = results[0]['if_score']

            result['rank_importance'] = count
            result['score'] = (result['if_score']/best_if + result['rank_relevance'])/2 #assume the best 
            result['reverse_score'] = result['score']
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
       # print companyScore
       # print results
        #print ','.join(map(str, companyScore.keys())) 
        
        #retrieve  info
        db = dbconnector().getNewCon()
        cur = db.cursor() 
        query = ("SELECT name, url, comp_id  FROM companies where  comp_id in (" + ','.join(map(str, companyScore.keys())) + ")")
        cur.execute(query)
        #print results
        for (name, url, comp_id ) in cur:
            companyScholars = []

            for result in results:
                if (result['company']) == (comp_id):
                    companyScholars.append(result)
                    
            companyScholars = sorted(companyScholars, key= itemgetter("reverse_score"), reverse=True )
            authorSummary = self.getAuthorSummary(companyScholars)
            conceptSummary = self.getConceptSummary(companyScholars)
            
            hits = len(companyScholars) 
            if hits > pub_per_comp:
                companyScholars = companyScholars[0:pub_per_comp]
                
                
            if hits > 0:        
                outputinfo.append({"company": comp_id, "company_name": name, "score": companyScore[comp_id], "hits" : hits, "url": url, 
                                   "author_summary": authorSummary, "concept_summary": conceptSummary, "publication": companyScholars}) #
            
        cur.close()
        db.close()
        
        outputinfo = sorted(outputinfo, key= itemgetter("score"), reverse=True)
        
        return outputinfo
        
    def getAuthorSummary(self, scholars, top=5):
        authors = []
        for scholar in scholars:
            if scholar['authors']:
                authors = authors + scholar['authors'].split("; ")
        if authors:        
            authors = [author.strip() for author in authors]
            author_group = self.groupItems(authors) #set([(key, len(list(group))) for key, group in groupby(authors) if key != u'...'])

            author_group_sort = sorted(author_group, key=lambda tup: tup[1], reverse=True)
        
            return author_group_sort[0:min(top, len(author_group_sort))]
        else:
            return None

    def getConceptSummary(self, scholars, top=5):
        concepts = []
        for scholar in scholars:
            if scholar['concepts']:
                concepts = concepts + scholar['concepts'].split("; ")
        if concepts:       
            concepts = [concept.strip()[1:] if concept.startswith(',') else concept.strip() for concept in concepts] 
                
            concept_group = self.groupItems(concepts) #set([(key, len(list(group))) for key, group in groupby(concepts) if key != u'...'])
            concept_group_sort = sorted(concept_group, key=lambda tup: tup[1], reverse=True)
            return concept_group_sort[0:min(top, len(concept_group_sort))]
        else:
            return None
    def groupItems(self, items):            
        output = [(key, items.count(key)) for key in set(items) if key != u'...' and key != u'']
        return output
        
    def getPrice(self):
        return random.randint(150, 400)
        
    def getAvailability(self):
        foo = ["in stock", "1 day", "2 days"]
        from random import choice
        return choice(foo)
    
    def getSchema(self):
        return Schema(title=TEXT(stored=True), path=ID(stored=True), company_name=TEXT(stored=True), content=TEXT(stored=True), article_title=TEXT(stored=True), authors=TEXT(stored=True), 
                      journal=TEXT(stored=True), year = NUMERIC(stored=True, sortable=True), sourceid = NUMERIC(stored=True), pmid = NUMERIC(stored=True), if_score = NUMERIC(stored=True, sortable=True), 
                      company = NUMERIC(stored=True), context=TEXT(stored=True), concept=TEXT(stored=True), source=TEXT(stored=True))
   
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
        return Schema(title=TEXT(stored=True), path=ID(stored=True), company_name=TEXT(stored=True), content=TEXT(stored=True), article_title=TEXT(stored=True), authors=TEXT(stored=True), 
                      journal=TEXT(stored=True), year = NUMERIC(stored=True, sortable=True), sourceid = TEXT(stored=True), pmid = NUMERIC(stored=True), if_score = NUMERIC(stored=True, sortable=True), company = NUMERIC(stored=True), context=TEXT(stored=True))
#test_index = indexer("../../data/indexer/companydb")
#test_index.clearIndexer
#test_index.loadByDb()
def storeQuery(query, ip):
    db = dbconnector().getNewCon()
    cur = db.cursor() 
    insert_query = ("insert into user_queries(query, ip, query_date) values(%s, %s, %s)")
    data_query = (query.encode('utf-8'), ip, datetime.datetime.now())
    cur.execute(insert_query, data_query)
    cur.close()
    db.commit()
    db.close()
    
def fulltext_search(query, ip=''):
    storeQuery(query, ip)
    test_searcher = searcher(settings.FULLTEXT_DIR)
    results = test_searcher.searchByKeyword(query) 
    results = test_searcher.rankResults(results)

    return (len(results), test_searcher.getCompanyInfo(results, 2))

def fulltext_search_filter_by_company_old(query, company, maximum=30):
    #print settings.FULLTEXT_DIR
    test_searcher = searcher(settings.FULLTEXT_DIR)
    results = test_searcher.searchByKeyword(query)
    results = test_searcher.rankResults(results)
    company_results = []
    for result in results:
        if str(result['company']) == str(company):
            company_results.append(result)
            if len(company_results) > maximum:
                break
    return (len(company_results), test_searcher.getCompanyInfo(company_results))

def fulltext_search_filter_by_company(query, company, author= '', concept = '', source = '', maximum=500):
    #print settings.FULLTEXT_DIR
    test_searcher = searcher(settings.FULLTEXT_DIR)
    results = test_searcher.searchByKeyword(query)
    results = test_searcher.rankResults(results)
    company_pubs = 0
    company_results = []
    for result in results:
        if str(result['company']) == str(company):
            company_pubs = company_pubs + 1
            #make sure every filter applies to the same number of publications
            if company_pubs > maximum:
                break
            #filter author or disease
            if author or concept or source:
                if author in result['authors'].split("; ") or author == '':
                    #should fix, for some reason, some concepts start with ,
                 if concept in  result['concepts'].split("; ") or  ","+concept in  result['concepts'].split("; ") or concept == '': 
                    if source == result['source'] or source == '': 
                        company_results.append(result)
                     
            else:
                company_results.append(result)
    return (len(company_results), test_searcher.getCompanyInfo(company_results))




#print searchByKeyword("ap1")
#print fulltext_search("EGFR")
#print fulltext_search_filter_by_company("ELISA", 670L) #Paul, Glidden