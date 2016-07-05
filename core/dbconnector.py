'''
Created on Jan 1, 2014

@author: binchen1
'''
#!/usr/bin/python
import mysql.connector
import MySQLdb

# you must create a Cursor object. It will let
#  you execute all the query you need
#cur = db.cursor() 

# Use all the SQL you like
#cur.execute("SELECT * FROM gscholar")

# print all the first cell of all the rows
#for row in cur.fetchall() :
    #print row[0]
    
class dbconnector(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
 # name of the data base

    def getDb(self):
        return self.db
    
    def getNewCon(self, database="sciencex"):
        self.db =   MySQLdb.connect(host="54.200.209.54", # your host, usually localhost
                     user="linkingpilot", # your username
                      passwd="linkingpilot123", # your password linkingpilot123
                      db=database)
        return self.db
    
    
    def  close(self):
        self.db.close()

#test = dbconnector()
#test.getNewCon()
#test.close()

