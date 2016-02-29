#!/usr/bin/python
# -*- coding: utf-8 -*-

# Json libs
from pprint import pprint
import json
import urllib,urllib2

# General libs
import datetime
import numpy as np
import sys
import time

# SQLite libs
import sqlite3 as lite


def UpdatePoints(cur,name,date,city,zipcode):
    # Get current visitors
    cur.execute('SELECT Visitors FROM Zips WHERE Zip == "'+str(zipcode)+'"')
    visitors=cur.fetchone()[0]
    
    points=0
    if visitors == 0:            
        # Register first person in zipcode
        print(name.encode('utf-8')+" is first in Zip "+str(zipcode)+"!")
        cur.execute('UPDATE Participants SET First = (SELECT First FROM Participants WHERE Name == "'+name+'")+1  WHERE Name == "'+name+'"')
        cur.execute('UPDATE Zips SET First_Name = "'+name+'" WHERE Zip == "'+str(zipcode)+'"')

    visitors+=1
    if (visitors == 1):
        points = 10
    elif visitors == 2:
        points = 8
    elif visitors == 3:
        points = 6
    elif visitors == 4:
        points = 5
    elif visitors == 5:
        points = 4
    elif visitors == 6:
        points = 3
    elif visitors == 7:
        points = 2
    else:
        points = 1

    # Update participants points
    cur.execute('UPDATE Participants SET Points = (SELECT Points FROM Participants WHERE Name == "'+name+'")+'+str(points)+'  WHERE Name == "'+name+'"')

    # Update visited counter
    cur.execute('UPDATE Zips SET Visitors = (Visitors + 1) WHERE Zip == "'+str(zipcode)+'"')

    cur.execute('SELECT Visitors FROM Zips WHERE Zip == "'+str(zipcode)+'"')
    print(name.encode('utf-8')+" was number "+str(visitors)+" in "+city.encode('utf-8'))
    
if __name__ == "__main__":

    con = None
    # Connect to database
    try:
        con = lite.connect('pdr.db')
        cur = con.cursor()    
        
    except lite.Error, e:
        
        print "Error %s:" % e.args[0]
        sys.exit(1)

    # Remove all points before rebuild
    cur.execute("Update Participants SET Points = 0")
    cur.execute("Update Participants SET First = 0")
    cur.execute("Update Zips SET Visitors = 0")
                
    # Fetch all records in chrono order
    cur.execute("SELECT * FROM Beers ORDER BY Drank_on")
    for ent in cur.fetchall():
        UpdatePoints(cur, ent[0], ent[1], ent[2], ent[3])

    con.commit()
    con.close()
    print("Done")
