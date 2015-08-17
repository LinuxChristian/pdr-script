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

# KML libs
from pykml import parser
from pykml.factory import KML_ElementMaker as KML
from lxml import etree

# Plotting
from matplotlib import cm

# Data wrangeling
import pandas as pd

'''
####################
#                  #
#  MAP FUNCTIONS   #
#                  #
####################
'''

'''
This function writes the main part of the map
index.html file

INPUT:
parti - List of participants
'''
def WriteMapIndex(parti):
    s = '''
    <!DOCTYPE html>
    <html>
            <head>
                    <title>Postnr Danmark Rundt</title>
                    <meta charset="utf-8" />
                    <link rel="stylesheet" href="http://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.3/leaflet.css" />
                    <link rel="stylesheet" type="text/css" href="css/own_style.css">
                    <script src="http://code.jquery.com/jquery-1.11.1.min.js"></script>
                    <script src="http://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.3/leaflet.js"></script>
                    <script src="js/leaflet-hash.js"></script>
                    <script src="js/Autolinker.min.js"></script>
                    <meta name="viewport" content="initial-scale=1.0, user-scalable=no" />
            </head>
            <body>
                    <div id="map"></div>
                    <input id="slide" type="range" min="0" max="1" step="0.1" value="1" onchange="updateOpacity(this.value)">\n
<script src="latest/exp_Sjaelland.js"></script>
<script src="latest/exp_Fyn.js"></script>
<script src="latest/exp_Jylland.js"></script>\
'''

    # Add list of user data files
    for p in parti:
#        print(p[1])
        s+='<script src="latest/exp_'+(p[1].replace(' ','')).encode('ascii','ignore').replace('.','')+'.js"></script>\n'

    s+='''
            <script>
            var map = L.map('map', {
                    zoomControl:true, maxZoom:19
            }).fitBounds([[53.7465326518,7.56974247323],[57.8457433581,15.0093935068]]);
            var hash = new L.Hash(map);
            var additional_attrib = 'created by Christian Braedstrup';
            var feature_group = new L.featureGroup([]);
            var raster_group = new L.LayerGroup([]);
            var basemap_0 = L.tileLayer('http://{s}.tile.thunderforest.com/outdoors/{z}/{x}/{y}.png', { 
                    attribution: additional_attrib 
            });	
            basemap_0.addTo(map);	
            var layerOrder=new Array();
    '''
        
    return s

'''
This function writes the user data to the index

INPUT:
p - Name of Participant

'''
def WriteMapParti(p,i):

    shortname = (p[1].replace(' ','')).encode('ascii','ignore').replace('.','')
    c = np.multiply(cm.Paired(i*10)[:3],255)
    s = '''
    function pop_'''+shortname+'''(feature, layer) {					
    var popupContent = '<table><tr><th scope="row">Navn</th><td>' + Autolinker.link(String(feature.properties['Navn'])) + '</td></tr><tr><th scope="row">Postnummer</th><td>' + Autolinker.link(String(feature.properties['Postnummer'])) + '</td></tr><tr><th scope="row">By</th><td>' + Autolinker.link(String(feature.properties['By'])) + '</td></tr><tr><th scope="row">Dato</th><td>' + Autolinker.link(String(feature.properties['Dato'])) + '</td></tr></table>';
    layer.bindPopup(popupContent);
    }

    function doStyle'''+shortname+'''(feature) {
    return {
    color: '#000000',
    fillColor: '#'''+'%02x%02x%02x' % (c[0], c[1], c[2])+'''',
    weight: 1.3,
    dashArray: '',
    opacity: 0.466666666667,
    fillOpacity: 0.466666666667
    };'''
    
    s+='''}
    var exp_'''+shortname+'''JSON = new L.geoJson(exp_'''+shortname+''',{
    onEachFeature: pop_'''+shortname+''',
    style: doStyle'''+shortname+'''
    });
    layerOrder[layerOrder.length] = exp_'''+shortname+'''JSON;
    for (index = 0; index < layerOrder.length; index++) {
    feature_group.removeLayer(layerOrder[index]);feature_group.addLayer(layerOrder[index]);
    }
    //add comment sign to hide this layer on the map in the initial view.
    feature_group.addLayer(exp_'''+shortname+'''JSON);
        '''
    return s;

'''
Writes the remaining part of the index file.

INPUT:
parti - List of participants
'''
def WriteMapFooter(parti):
    # Write all zipcodes to map
    s = '''
    function pop_Postnumre(feature, layer) {					
    var popupContent = '<table><tr><th scope="row">Postnummer</th><td>' + Autolinker.link(String(feature.properties['POSTNR_TXT'])) + '</td></tr><tr><th scope="row">Navn</th><td>' + Autolinker.link(String(feature.properties['POSTBYNAVN'])) + '</td></tr></table>';
            layer.bindPopup(popupContent);
    }

    function doStyleDanskepostnumre(feature) {
                    return {
                            color: '#000000',
                            fillColor: '#4706d4',
                            weight: 0.5,
                            dashArray: '0',
                            opacity: 1.0,
                            fillOpacity: 0.0
                    };

    }
    var exp_SjaellandJSON = new L.geoJson(exp_Sjaelland,{
            onEachFeature: pop_Postnumre,
            style: doStyleDanskepostnumre
    });
    layerOrder[layerOrder.length] = exp_SjaellandJSON;

    var exp_FynJSON = new L.geoJson(exp_Fyn,{
            onEachFeature: pop_Postnumre,
            style: doStyleDanskepostnumre
    });
    layerOrder[layerOrder.length] = exp_FynJSON;

    var exp_JyllandJSON = new L.geoJson(exp_Jylland,{
            onEachFeature: pop_Postnumre,
            style: doStyleDanskepostnumre
    });
    layerOrder[layerOrder.length] = exp_JyllandJSON;

    }

    '''
    
    s += '''
    feature_group.addTo(map);
    var title = new L.Control();
    title.onAdd = function (map) {
    this._div = L.DomUtil.create('div', 'info'); // create a div with a class "info"
    this.update();
    return this._div;
    };
    title.update = function () {
    this._div.innerHTML = '<h2>Postnr Danmark Rundt</h2>Status: '''+datetime.date.today().strftime("%d %b %Y")+''' '
    };
    title.addTo(map);
    var baseMaps = {
    'Thunderforest Outdoors': basemap_0
    };
    L.control.layers(baseMaps,{"Sjaelland": exp_SjaellandJSON,
    "Fyn": exp_FynJSON,
    "Jylland": exp_JyllandJSON,
    '''

    for i,p in enumerate(parti):
        shortname = (p[1].replace(' ','')).encode('ascii','ignore').replace('.','')
        s+='"'+p[1]+'": exp_'+shortname+"JSON"
        if i < len(parti)-1:
            s+=','
            
    s+='''},{collapsed:true}).addTo(map);
    function updateOpacity(value) {
    }
    L.control.scale({options: {position: 'bottomleft',maxWidth: 100,metric: true,imperial: false,updateWhenIdle: false}}).addTo(map);
    </script>
    </body>
    </html>

    '''
    return s;

'''
Combined function to write new participants
into the index.html file

INPUT:
plist - List of all participants
'''
def WriteMap(plist):
    s = ''
    s+=WriteMapIndex(plist)
    
    for i,p in enumerate(plist):
        s+=WriteMapParti(p,i)

    s+=WriteMapFooter(plist)

    with open('/tmp/maps/index.html','w') as f:
        f.write(s.encode('utf-8'))

'''
####################
#                  #
#  MAP FUNCTIONS   #
#                  #
####################
'''
def WriteHeader(name):
    # Write the first part
    s = '''var exp_'''+(name.replace(' ','')).encode('ascii','ignore').replace('.','')+''' = {
    "type": "FeatureCollection",
    "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
    
    "features": [\n'''

    return s

'''
This function writes the current location
polygon to json format for leaflet.

Polygons can either be single or in a
multipolygon structure.
'''
def WritePolygon(data,place):
#
    s = ""
    try:
        s += '''{ "type": "Feature", "properties": {"Navn":"'''+data[0]
        s += '''","Postnummer":"'''+str(data[3])
        s += '''","By":"'''+data[2]
        s += '''","Dato":"'''+str(data[1])+'''"}, "geometry":{"type":'''
        
        # Parse polygons
        if hasattr(place,"MultiGeometry"):
            poly = place.MultiGeometry.Polygon;
            s=s+'''"MultiPolygon","coordinates":[ [ '''
        else:
            poly = place.Polygon;
            s=s+'''"Polygon","coordinates":[ '''

        # Loop over geometries
        for i,pol in enumerate(poly):
            pol = str(pol.outerBoundaryIs.LinearRing.coordinates)
            # Old way
            #p = np.array([x.split(',') for x in (pol.split(' '))]).astype(np.float)
            #s=s+np.array_str(p).replace('\n',', ')

            arr = np.array([np.fromstring(x,dtype=np.float,sep=',') for x in pol.split(' ')])
            s+=np.array2string(arr,separator=',').replace('\n','').replace(' ','')

            # Write comma if multiple polygons
            if len(poly)-1 == i:
                # Support for MultiGeometry
                if hasattr(place,"MultiGeometry"):
                    s=s+''']] } }'''
                else:
                    s=s+'''] } }'''
            else:
                s=s+''' ], [ '''

    except:
        print("Failed to parse record!")
        print(data)
        print(place)

    return s;

'''
This function writes the ende of file
'''
def WriteFooter():
    return '\n]\n}'

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
#    if "place" in post:
#        print("Found GPS data.. haps haps haps")
        
    # Split message on newline
    msg = post["message"].encode('utf-8').split('\n')
    print(msg)
    
    # Get zipcode
    szipcode = [s for s in msg[0].split(" ") if (s.isdigit() and len(s)==4)]
    
    if len(szipcode) > 0:
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
    else:
        print("Invalid post!")
        print(msg)
        return None
    
'''
####################
#                  #
#  DATABASE FUNC   #
#                  #
####################
'''

# Fill initial values of visitors in Zip and points
# NOTE: THIS FUNC SHOULD ONLY BE CALLED ONCE
def InitVisitors(cur):
    # Get all zips
    cur.execute("SELECT * FROM Zips")
    zips=cur.fetchall()

    # Loop over all zips
    for z in zips:
        cur.execute("SELECT count(*) FROM Beers WHERE Zipcode == "+z[1])
        res = cur.fetchall()
        # Insert count into table
        cur.execute("INSERT INTO Zips(Visitors) VALUES (?)",res[0])
        
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

    cur.execute('''INSERT OR REPLACE INTO Beers(Participant, Drank_on, City, Zipcode,Image) VALUES(?,?,?,?,?)''',(name,date,city,zipcode,image))
    
    # Update with GPS
    if lat is not None and lon is not None:
        cur.execute('''INSERT INTO Beers(Lat,Lon) VALUES(?,?) WHERE Participant == "'''+name+'''" and Zipcode == "'''+zipcode+'''"''',(lat,lon))

    # Update with beer name
    if beer is not None:
        cur.execute('''INSERT INTO Beers(Beer) VALUES(?) WHERE Participant == "'''+name+'''" and Zipcode == "'''+zipcode+'''"''',(beer))

    # Update visitor database
    
def UpdateUserDatabase(cur,userdb):
    cur.execute('''INSERT OR IGNORE INTO Participants(name) VALUES(?)''',(userdb,))

'''
Main function

- Sets up connection to database
- Checks facebook for updates
- Writes new beers and users to the database
- Updates the main map
'''
if __name__ == "__main__":
    con = None
    
    # Connect to database
    try:
        con = lite.connect('pdr.db')
        cur = con.cursor()    

    except lite.Error, e:

        print "Error %s:" % e.args[0]
        sys.exit(1)


    stats = []
    offline=False

    # Get last update in epoch time
    cur.execute("SELECT Drank_on FROM Beers ORDER BY Drank_on DESC")
    latest=cur.fetchone()[0]
    latest_epoch=int(time.mktime(time.strptime(latest,'%Y-%m-%d %H:%M:%S')))
    
    ############################
    #     FACEBOOK STUFF       #
    ############################
    # First visit https://developers.facebook.com/tools/explorer for an one hour token
    # See http://stackoverflow.com/questions/12168452/long-lasting-fb-access-token-for-server-to-pull-fb-page-info#
    token=str(np.loadtxt('token.txt',dtype=np.str))

    # August 1th in epoch 1438372800
    facebookurl = 'https://graph.facebook.com/1630748980524187/feed?fields=full_picture,message,from,id,link,created_time&date_format=U&access_token='+token+'&since='+str(latest_epoch)
    # 1630748980524187/feed?access_token='+token+'&since='+str(latest_epoch)+'&limit=100&date_format=U'

    print("Fetching data from Facebook after "+latest)
    if offline is True:
        with open('../offline_feed_06_08_2015.json') as jsondata:
            data = json.load(jsondata)
    else:
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
    PMN = [str(x) for x in root.Document.findall("Placemark/name")]

    print("Found "+str(len(data['data']))+" records")
    
    ############################
    #      UPDATE TABLE        #
    ############################
    for post in data['data']:
        if ('full_picture' in post) and ('message' in post):
            entry = ParseFacebook(post)

            # Check for new participants
            cur.execute('SELECT * FROM Participants WHERE Name = "'+entry[0]+'";')
            if cur.fetchone() is None:
                print("Found new participant.. "+entry[0]+".. Adding to DB!")
                UpdateUserDatabase(cur,entry[0])

            # Commit beer entry to database
            if entry is not None:
                UpdateBeerDatabase(cur,entry)
                con.commit()
                
    ############################
    #      WRITE MAP DATA      #
    ############################
    # Get data for zipcode
    cur.execute('SELECT * FROM Participants;')
    participants = cur.fetchall()
    for p in participants:
        cur.execute('SELECT * FROM Beers WHERE Participant = "'+p[1]+'";')
        s = WriteHeader(p[1].encode('ascii','ignore'));

        beers = cur.fetchall()
        for i,b in enumerate(beers):
            try:
                place = PM[PMN.index(str(b[3]))]    
            except e:    
                print "Error %s:" % e.args[0]
                sys.exit(1)

            s=s+WritePolygon(b,place)

            if i < len(beers)-1:
                s += ',\n'


        s += WriteFooter()

        with open('/tmp/maps/exp_'+(p[1].replace(' ','')).encode('ascii','ignore').replace('.','')+'.js','w') as f:
            f.write(s.encode('utf-8'))

    WriteMap(participants)

'''
 COMPUTE STATISTICS
'''

# Compute participant stats
cur.execute("SELECT Participant,count(),count()/593.0,(julianday('2020-08-01')-julianday('now'))/(593.0-count()) FROM Beers GROUP BY Participant ORDER BY count() DESC")

stats = pd.DataFrame(cur.fetchall())
stats.columns = ["Navn","Postnumre","Dækning antal (%)","DPP*"]


# Compute area visited
cur.execute("SELECT sum(Zips.area) FROM Beers INNER JOIN Zips ON Beers.Zipcode=Zips.zip GROUP BY Beers.Participant ORDER BY count() DESC")
area = stats.insert(2,'Area',[f[0] for f in cur.fetchall()])

# Fetch beers the last 7 days - Old Green Jersy
#cur.execute("SELECT Participant,count() FROM Beers WHERE Drank_on >= datetime('now','-7 days') GROUP BY Participant")

cur.execute("SELECT Participant, count(*) FROM (SELECT * FROM Beers GROUP BY Zipcode ORDER BY Drank_on) GROUP BY Participant")
rate=pd.DataFrame(cur.fetchall())
rate.columns = ["Navn","FIP"]
stats=pd.merge(stats,rate,on="Navn")

#stmp=stats.copy(deep=True)
yellow=stats["Navn"][0]
green=(stats.sort("FIP",ascending=False))["Navn"].iloc[0]

if (yellow == green):
    green=(stats.sort("FIP",ascending=False))["Navn"].iloc[1]

polka=(stats.sort("Area",ascending=False))["Navn"].iloc[0]
if (yellow == polka):
    polka=(stats.sort("Area",ascending=False))["Navn"].iloc[1]

stats.columns = ["Navn","Postnumre","Dækning Areal (%)","Dækning antal (%)","DPP","FIP"]

s=u'''<link rel="stylesheet" type="text/css" href="table.css">
 <table align="center" class="jersy">
  <thead>
    <tr width="75%">
      <th>Føre</th>
      <th>Sprinter</th>
      <th>Areal</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><img width="150px" height="120px" src="yellow.png"></img></td>
      <td><img width="150px" height="120px" src="green.png"></img></td>
      <td><img width="150px" height="120px" src="polkadot.png"></img></td>
    </tr>
    <tr>
      <td>'''+yellow+'''</td>
      <td>'''+green+'''</td>
      <td>'''+polka+'''</td>
    </tr>
  </tbody>
 </table>
</br>
'''
s+=stats.to_html(index=False,classes=["scoreboard"])


with open("/tmp/table.html", "w") as text_file:
    text_file.write(s.encode('utf-8'))


con.close()

print("DONE!")
