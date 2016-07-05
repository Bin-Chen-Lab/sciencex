'''
utilities to contact PubMED
Create on July 2013
@author: Bin Chen
'''
import urllib
import xml.etree.ElementTree as ET
import re
import codecs
import math
import time
import json
from journal import journal
from datetime import date

class paper():
    def __init__(self, paper_root):
                self.paper_root = paper_root

    def get_meta_string(self):       
        return self.getAuthors() + ' (' + self.get_pub_year() + ') ' + self.get_title() + ' ' + self.get_journal_title() + ' ' + self.get_issue() + ': ' + self.get_pages() + '. ' # + 'DOI: ' + self.get_doi() + '.' 
    
    def get_journal_title(self):
        return self.paper_root[0].findtext(".//ISOAbbreviation", default='')

    def get_title(self):
        return self.paper_root[0].findtext(".//ArticleTitle", default='')
    
    def get_pub_year(self):
        return self.paper_root[0].findtext(".//PubDate/Year", default='')

    def get_pub_month(self):
        return self.paper_root[0].findtext(".//ArticleDate/Month", default='')

    def get_pub_date(self):
        return self.paper_root[0].findtext(".//ArticleDate/Day", default='')
    
    def get_issue(self):
        return self.paper_root[0].findtext(".//Issue", default='')

    def get_pages(self):
        return self.paper_root[0].findtext(".//MedlinePgn", default='')

    def get_doi(self):
        return self.paper_root[0].findtext(".//ELocationID", default='')

    def get_abstract(self):
        return self.paper_root[0].findtext(".//AbstractText", default='')
    
    def get_pmcid(self):
        return self.paper_root[1].findtext(".//ArticleId[@IdType='pmc']", default='')
        
    def get_mesh(self):
        meshes = self.paper_root[0].findall(".//MeshHeading")
        mesh_terms = []
        for mesh in meshes:
            mesh_term = mesh.findtext(".//DescriptorName",default='')
            mesh_terms.append(mesh_term)
            
        return '; '.join(mesh_terms)

    def get_pmid(self):
        return self.paper_root[0].findtext(".//PMID", default='')

    def get_corr_author(self):
        author_list = self.getAuthorList()
        #assume the corresponding author appears in the last
        #some papers have no author
        if len(author_list) > 1:
            return author_list[-1]
        else: 
            return ''
        
    # return a list of author names
    def getAuthorList(self):
        authorList=[]
        author_elements = self.paper_root[0].findall(".//Author")
        if author_elements == None: 
            return authorList

        for author_element in author_elements:
            last_name = author_element.findtext(".//LastName", default='')
            initial_name = author_element.findtext(".//Initials", default='')
            authorList.append(last_name + ' ' + initial_name )

        return authorList

    def getAuthors(self):
        author_list = self.getAuthorList()
        if len(author_list) > 4:           
            return ', '.join(author_list[0:4]) + ', et al.'
        else:
            return ', '.join(author_list)     
               
    def getAuthorsAbbrev(self):
        author_list = self.getAuthorList()
        if len(author_list) > 4:           
            return ', '.join(author_list[0:4]) + ', ..., ' + author_list[len(author_list)-1]
        else:
            return ', '.join(author_list)   
            
    def get_author_full_names(self):
        #should have a better way
        authorList=[]
        author_elements = self.paper_root[0].findall(".//Author")
        if author_elements == None: 
            return authorList

        for author_element in author_elements:
            last_name = author_element.findtext(".//LastName", default='')
            first_name = author_element.findtext(".//ForeName", default='')
            authorList.append(first_name + ' ' + last_name )

        return '; '.join(authorList)
    
    
class pubmed_utilities():
#basic pubmed utilities
        
        def __init__(self):
                self.title = ''
        
        def _removeNonAscii_(self, s): return ''.join([i if ord(i) < 128 else ' ' for i in s])
        
        def _html_decode_(self, s):
            """
            Returns the ASCII decoded version of the given HTML string. This does
            NOT remove normal HTML tags like <p>.
            """
            htmlCodes = (
                    ("'", '&#39;'),
                    ('"', '&quot;'),
                    ('>', '&gt;'),
                    ('<', '&lt;'),
                    ('&', '&amp;')
                    )
            for code in htmlCodes:
                s = s.replace(code[1], code[0])
            return s
        

        def get_papers(self, field, value, affiliation="", since_year="", since_month= 1, abstract="yes", retmax=50):
            if since_year == "":
                since_year = str(date.today().year - 8)
            
            value = self._removeNonAscii_(self._html_decode_(value))
            pmids = self.get_pmids(field, value, since_year, since_month, retmax,affiliation)
            paper_metas = []
            if len(pmids) > 0:
                paper_metas = self._get_paper_meta( ','.join(pmids), abstract)

            return paper_metas
            
        def get_pmids(self, field, value, since_year, since_month, retmax, affiliation=""):
            if field == "author":
                field_value = '('+value+'[Full Author Name]'+')'
            elif field == "title":
                field_value = '('+value+'[Title]'+')' 
            else:
                field_value = value
                   
            target_year =  "" # '(' + str(since_year) + '/' + str(since_month) + '[Date - Publication] : 3000[Date - Publication])' #only show the pub in the last 8 years by default
            if affiliation != "":
                affiliation = '('+affiliation+'[Affiliation]'+')'
                url = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed" + "&RetMax=" + str(retmax) + "&term="  + field_value + " AND " + affiliation  + " AND " + target_year 
            else:
                url = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed" + "&RetMax=" + str(retmax) + "&term="  + field_value   + " AND " + target_year 
                
            rss = ET.parse(urllib.urlopen(url)).getroot()
            print(url)
            pmids = []
            for id in rss.findall('./IdList/Id'):
                pmids.append(id.text)

            return pmids


        
        def _get_paper_meta(self, pmids, abstract):
            url = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=" + str(pmids) + "&rettype=xml"
            response = urllib.urlopen(url)
            all_paper_roots = ET.parse(response).getroot()
            paper_metas = []
            for i in range(0, len(all_paper_roots)):
                paper_meta = {}
                paper_info = paper(all_paper_roots[i])

                paper_meta["summary"] = paper_info.get_meta_string()
                paper_meta["title"] = paper_info.get_title()                
                paper_meta["Journal"] = paper_info.get_journal_title()
                paper_meta["PubMedID"] = paper_info.get_pmid()
                paper_meta["PMCID"] = paper_info.get_pmcid()
                paper_meta["PublicationDate"] = paper_info.get_pub_year() + " " + paper_info.get_pub_month() + " " + paper_info.get_pub_date() 
                paper_meta["Keyword"] = paper_info.get_mesh()
                if abstract == "yes":
                    paper_meta["Abstract"] = paper_info.get_abstract()
                    
                paper_meta["author"] = paper_info.get_author_full_names()
                paper_meta["corresponding author"] = paper_info.get_corr_author()
                
                paper_metas.append(paper_meta)
                
            return paper_metas
        
        
        def get_paper_meta_summary(self, pmid):
            url = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=" + str(pmid) + "&rettype=xml"
            response = urllib.urlopen(url)
            all_paper_roots = ET.parse(response).getroot()
            paper_metas = []
            for i in range(0, len(all_paper_roots)):
                paper_meta = {}
                paper_info = paper(all_paper_roots[i])

                paper_meta["summary"] = paper_info.getAuthorsAbbrev() + "\t" + paper_info.get_title() + "\t" + paper_info.get_journal_title() + "\t" + paper_info.get_pub_year() 
                
                paper_metas.append(paper_meta)
                
            return paper_metas

        def check_author_know_antigen(self,author,antigen):

                author = '('+author+'[Full Author Name]'+')'
                if not antigen.startswith('anti-'):
                        antigen = "anti-" + antigen

                target_year =  '(' + str(date.today().year - 8) + '[Date - Publication] : 3000[Date - Publication])' #only show the pub in the last 8 years by default


                #search PMC, maximum return 100 articles, as we only need too many articles for an antigen
                url = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed" + "&RetMax=100" + "&term="  + author + " AND " + antigen  + " AND " + target_year
                rss = ET.parse(urllib.urlopen(url)).getroot()
                pmc_ids = []
                print url
                for err in rss.findall('./ErrorList/PhraseNotFound'):
                        if (err.text == antigen):
                                return False
                        
                if int(rss.findtext('./Count')) > 0 :
                        return True
                else:
                        return False

        def build_antigen_library(self):
            with  open("data/antigenquestions.csv","r") as f:
                antigens = f.readlines()[0].split("\r")
            return antigens
        
        def get_antigens_by_author(self,author):
                #search pmc, find the antigens the author likely used
                #for each author and each antigen, we have to make a call to the pmc api, this may bring too much traffic to PMC, we should figure out a better way
                antigen_library = self.build_antigen_library()
                antigens = []
                for antigen in antigen_library:
                        print 'checking author ' + author + ' and antigen ' + antigen
                        if self.check_author_know_antigen(author,antigen):
                                antigens.append(antigen)
                return antigens
            
#pubmed = pubmed_utilities()
#print(pubmed.get_antigens_by_author('Nicholas Mordwinkin'))
#print(pubmed.check_author_know_antigen('Masae Naruse' ,'CD44'))
#print(pubmed.get_papers('', 'Codon optimisation to improve expression of a Mycobacterium avium ssp. paratuberculosis-specific membrane-associated antigen by Lactobacillus salivarius', abstract="no"))
#print(pubmed.get_paper_meta_summary('23620276')[0]['summary'])
#print(pubmed.get_paper_meta('22859915'))
