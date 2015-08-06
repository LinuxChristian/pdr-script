#!/usr/bin/python
# -*- coding: utf-8 -*-

# Json libs
from pprint import pprint
import json
import urllib,urllib2

# General libs
import datetime
import numpy as np

# SQLite libs
import sqlite3 as lite

# KML libs
from pykml import parser
from pykml.factory import KML_ElementMaker as KML
from lxml import etree

con = None

def WriteDataFile(data,poly):
    # Write the first part
    s = '''var exp_ChristianFredborgBrdstrupany = {
    "type": "FeatureCollection",
    "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
    
    "features": [
    { "type": "Feature", "properties": {'''+'''},"Geometry":{"type",'''

    # Parse polygons
    if hasattr(place,"MultiGeometry"):
        poly = place.MultiGeometry.Polygon;
        s=s+'''"MultiPolygon","coordinates":[['''
    else:
        poly = place.Polygon;
        s=s+'''"Polygon","coordinates":['''
        
    # Loop over geometries
    for i,pol in enumerate(poly):
        pol = str(pol.outerBoundaryIs.LinearRing.coordinates)
        p = np.array([x.split(',') for x in (pol.split(' '))]).astype(np.float)
        s=s+np.array_str(p).replace('\n',', ')

        # Write comma if multiple polygons
        if len(poly)-1 == i:
            s=s+''']]}}'''
        else:
            s=s+'''],['''
            

    s = s+']}'
    return s;

######################
#   Facebook Post    #
######################
def ParseFacebook(post):
    name=None
    msg=None
    zipcode=None
    lat=None
    lon=None
    image=None
    date=None
    town=None
    
    t = datetime.datetime.fromtimestamp(float(post["created_time"]))
    date = t.strftime('%Y-%m-%d %H:%M:%S')
    name = post["from"]["name"]
        
    # Grab GPS if it exists
    if "place" in post:
        print("Found GPS data.. haps haps haps")
        
    # Split message on newline
    msg = post["message"].encode('utf-8').split('\n')

    # Get zipcode
    szipcode = [s for s in msg[0].split(" ") if (s.isdigit() and len(s)==4)]
    zipcode = int(szipcode[0])
    
    # Fix combined zipcodes
    if zipcode < 1500:
        zipcode = "1000 - 1499"
    elif zipcode >= 1500 and zipcode < 1800:                                        zipcode = "1500 - 1799"
    elif zipcode >= 1800 and zipcode < 2000:                                        zipcode = "1800 - 1999"

    # Validate zipcode
    cur.execute("SELECT * FROM Zips WHERE zip == '"+str(zipcode)+"'")
    z = cur.fetchone();

    if (z is None):
        print("Invalid zipcode!");
    else:
        # Get town
        town = z[0]

    return [name,date,zipcode,town,lat,lon,image]

# Create the database
def CreateDatabase(cur):
    cur.execute("CREATE TABLE Participants(Userid INT PRIMARY KEY, Name TEXT UNIQUE, Joined_on DATE)")
    cur.execute("CREATE TABLE Beers(Participant TEXT, Drank_on DATE, City TEXT, Zipcode INT, Image TEXT, Lat FLOAT, Lon FLOAT, Beer TEXT, CONSTRAINT unq UNIQUE (Participant, zipcode))")


def UpdateBeerDatabase(cur,
                       e):
    name=e[0]#.decode('unicode-escape') # Participant name
    date=e[1] # Beer drank on date
    city=e[3]
    zipcode=e[2]
    image=e[6] # Link to image
    lat = e[4] # Latitude
    lon = e[3] # Longitude
    beer = None # Name of beer

    # OR IGNORE
    cur.execute('''INSERT OR IGNORE INTO Beers(Participant, Drank_on, City, Zipcode,Image) VALUES(?,?,?,?,?)''',(name,date,city,zipcode,image))

    # Update with GPS
    if lat is not None and lon is not None:
        cur.execute('''INSERT INTO Beers(Lat,Lon) VALUES(?,?) WHERE Participant == "'''+name+'''" and Zipcode == "'''+zipcode+'''"''',(lat,lon))

    # Update with beer name
    if beer is not None:
        cur.execute('''INSERT INTO Beers(Beer) VALUES(?) WHERE Participant == "'''+name+'''" and Zipcode == "'''+zipcode+'''"''',(beer))

def UpdateUserDatabase(cur,userdb):
    cur.execute('''INSERT OR IGNORE INTO Participants(name) VALUES(?)''',(userdb,))


    
# Connect to database
try:
    con = lite.connect('pdr.db')
    
    cur = con.cursor()    
    cur.execute('SELECT SQLITE_VERSION()')
    
    data = cur.fetchone()
    
    print "SQLite version: %s" % data                
    
except lite.Error, e:
    
    print "Error %s:" % e.args[0]
    sys.exit(1)
    
        
#CreateDatabase(cur)
#for u in parti:
#    print(u[0])
#    UpdateUserDatabase(cur,u[0])

#cur.execute('SELECT * FROM Participants;')
#print(cur.fetchall())
#con.commit()

stats = []

############################
#     FACEBOOK STUFF       #
############################
# First visit https://developers.facebook.com/tools/explorer for an one hour token
token=str(np.loadtxt('token.txt',dtype=np.str))

facebookurl = 'https://graph.facebook.com/1630748980524187/feed?access_token='+token+'&since=1438372800&limit=100&date_format=U'

print("Fetching data from Facebook")
response = urllib2.urlopen(facebookurl)

# Check for HTTP codes other than 200
if response.code != 200:
    print('Status:', response.code, 'Problem with the request. Exiting.')
    exit()

# Decode the JSON response into a dictionary and use the data
jsondata = response.read()
data = json.loads(jsondata)

############################
#    Get ZIP POLYGONS      #
############################
root = parser.fromstring(open('Danske_postnumre.kml','r').read())

# Get Placemarks
PM = root.Document.findall("Placemark")
PMN = root.Document.findall("Placemark/name")

############################
#      UPDATE TABLE        #
############################
for post in data['data']:
    if ('picture' in post) and ('www.google.com' not in post['picture']) and ('message' in post):
        entry = ParseFacebook(post)
        UpdateBeerDatabase(cur,entry)
        con.commit()
        
############################
#      WRITE MAP DATA      #
############################
    # Get data for zipcode
#    place = PM[PMN.index(entry[2])]
#    print(WriteDataFile(entry,place))
#            print(p)

con.close()
