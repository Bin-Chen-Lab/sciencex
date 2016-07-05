'''
Created on Jan 2, 2015

@author: binchen1
'''
if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))


from searcher import searcher

from django.conf import settings

from dbconnector import dbconnector
import csv 


def getHits(searcher, keyword):
    results = searcher.searchByKeyword(keyword)

    pmids = []
    for result in results:
        if  result["pmid"] != None:
            pmids.append(str(result["pmid"]))   
    return pmids

def updateProduct():
    test_searcher = searcher(settings.FULLTEXT_DIR)
    csvfile = csv.writer(open('product_hits.csv', 'wb')  )
        
    db = dbconnector().getNewCon("product")
    cur = db.cursor() 
    cur.execute("select product from products  ")
    count = 0 
    for (product, ) in cur :
            count = count + 1
            print count
            hits = getHits(test_searcher, product)
            csvfile.writerow([product, "; ".join(hits), len(hits)])
            '''cur1 = db.cursor() 
            insert_query = ("update  products set hits = %s , num_hits = %s where product = %s")
            data_query = ("; ".join(hits), len(hits), product)
            cur1.execute(insert_query, data_query)
            cur1.close() 
            db.commit()'''
    cur.close()
    db.close()

def updateProductLocal():
    test_searcher = searcher(settings.FULLTEXT_DIR)
    csvfile = csv.writer(open('product_hits.csv', 'wb')  )
    count = 0    
    with open('../../../data/products.csv', 'rU') as csvinputfile:
        spamreader = csv.reader(csvinputfile)
        for row in spamreader:
            count = count + 1
            
            print count
            hits = getHits(test_searcher, row[0].strip())
            if len(hits) > 1:
                csvfile.writerow([row[0].strip(), "; ".join(hits), len(hits)])
            '''cur1 = db.cursor() 
            insert_query = ("update  products set hits = %s , num_hits = %s where product = %s")
            data_query = ("; ".join(hits), len(hits), product)
            cur1.execute(insert_query, data_query)
            cur1.close() 
            db.commit()'''

def getSimPairs():
    csvfile = csv.writer(open('product_product_sim.csv', 'wb')  )
    count = 0    
    with open('product_hits.csv', 'rU') as csvinputfile1:
        spamreader1 = csv.reader(csvinputfile1)
        for row1 in spamreader1:
            if row1[2] > 0:
                 with open('product_hits.csv', 'rU') as csvinputfile2:
                    spamreader2 = csv.reader(csvinputfile2)
                    for row2 in spamreader2:
                        if len(row2) ==3:
                            if row2[2] > 0:    
                                common = len(list(set(row1[1].split("; ")) & set(row2[1].split("; "))))
                                if common > 1:
                                    csvfile.writerow([row1[0].strip(), row2[0].strip(), row1[2], row2[2], common])    
            
#print getHits(test_searcher, "AP1")
#updateProductLocal()
#getSimPairs()