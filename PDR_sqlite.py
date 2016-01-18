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
from collections import OrderedDict

# Turn off pandas column width limitor
#if int((pd.version.short_version).split('.')[1]) >= 11:
pd.set_option('display.max_colwidth', -1)
#else:
#	pd.set_printoptions('display.max_colwidth', -1)


'''
####################
#                  #
# HELPER FUNCTIONS #
#                  #
####################
'''

'''
This function returns the epoch time from each json
response from facebook. This can then be used to sort
the facebook posts.

'''
def json_time(json):
    try:
        return int(json["created_time"])
    except KeyError:
        return 0

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
        '''

#    for (index = 0; index < layerOrder.length; index++) {
#    feature_group.removeLayer(layerOrder[index]);feature_group.addLayer(layerOrder[index]);
#   }
#    //add comment sign to hide this layer on the map in the initial view.
#    feature_group.addLayer(exp_'''+shortname+'''JSON);
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
    this._div.innerHTML = '<h2>Postnr Danmark Rundt</h2>Status: '''+datetime.date.today().strftime("%d %b %Y - %H:%m")+''' '
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

    with open('/home/pi/davfs/maps/latest/index.html','w') as f:
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
        s += '''","Dato":"'''+datetime.datetime.fromtimestamp(float(data[1])).strftime('%Y-%m-%d %H:%M:%S')+'''"}, "geometry":{"type":'''
        
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
    link=None
    date=None
    town=None
    beer=None
    
    date = int(post["created_time"])
    name = post["from"]["name"]
        
    # Grab GPS if it exists
    if "place" in post:
        print("Found GPS data.. haps haps haps")
        lat = float(post["place"]["location"]["latitude"])
        lon = float(post["place"]["location"]["longitude"])
        
    # Split message on newline
    msg = post["message"].encode('utf-8').split('\n')

    if u'Øl:'.encode('utf-8') in msg:
        beeridx = msg.lower().find(u'Øl:')
        beer=msg[beeridx+2:-1]

    link=post['link']
    image=post['full_picture']
    
    # Get zipcode
    szipcode = [s for s in msg[0].split(" ") if (s.isdigit() and len(s)==4)]
    
    if len(szipcode) > 0:
        zipcode = int(szipcode[0])
    
        # Fix combined zipcodes
        if zipcode < 1500:
            zipcode = "1000 - 1499"
        elif zipcode >= 1500 and zipcode < 1800:                                        zipcode = "1500 - 1799"
        elif zipcode >= 1800 and zipcode < 2000:                                        zipcode = "1800 - 1999"
        
        # Validate zipcode and grab zipcode name
        cur.execute("SELECT * FROM Zips WHERE zip == '"+str(zipcode)+"'")
        z = cur.fetchone();
            
        if (z is None):
            print("Invalid zipcode!");
	    print("Zip string: {}".format(szipcode));
        else:
            # Get town
            town = z[0]

        return [name,date,zipcode,town,lat,lon,image,beer,link]
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

def ResetPoints(cur,con):
    cur.execute('UPDATE Participants SET First = 0, Points = 0')
    cur.execute('UPDATE Zips SET Visitors = 0')
    cur.execute('DELETE FROM Beers')
    con.commit()
    
# Create the database
def CreateDatabase(cur):
    cur.execute("CREATE TABLE Participants(Userid INT PRIMARY KEY, Name TEXT UNIQUE, Joined_on DATE)")
    cur.execute("CREATE TABLE Beers(Participant TEXT, Drank_on INT, City TEXT, Zipcode INT, Image TEXT, Link TEXT, Lat FLOAT, Lon FLOAT, Beer TEXT, CONSTRAINT unq UNIQUE (Participant, zipcode))")


def UpdateBeerDatabase(cur,
                       e):
    name=e[0]#.decode('unicode-escape') # Participant name
    date=e[1] # Beer drank on date
    zipcode=e[2]
    city=e[3]
    lon = e[4] # Longitude
    lat = e[5] # Latitude
    image=e[6] # Link to image
    beer = e[7] # Name of beer
    link = e[8] # Link to facebook

    print("Updating User "+name.encode('utf-8'))
    print("With zipcode "+str(zipcode).encode('utf-8')+" and town "+city.encode('utf-8'))
    print("Drank on "+str(date))
    print("")
    
    # Update drinking information
    cur.execute('''INSERT OR REPLACE INTO tmp(Participant, Drank_on, City, Zipcode,Image,Link) VALUES(?,?,?,?,?,?)''',(name,date,city,zipcode,image,link))

    # Update with GPS
    if lat is not None and lon is not None:
        cur.execute('''INSERT INTO tmp(Lat,Lon) VALUES(?,?) WHERE Participant == "'''+name+'''" and Zipcode == "'''+zipcode+'''"''',(lat,lon))

    # Update with beer name
    if beer is not None:
        cur.execute('''INSERT INTO tmp(Beer) VALUES(?) WHERE Participant == "'''+name+'''" and Zipcode == "'''+zipcode+'''"''',(beer))

    
def UpdateUserDatabase(cur,userdb):
    cur.execute('''INSERT OR IGNORE INTO Participants(name) VALUES(?)''',(userdb,))


def UpdatePoints(cur,e):
    name=e[0]#.decode('unicode-escape') # Participant name
    date=e[1] # Beer drank on date
    city=e[2]
    zipcode=e[3]

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
    elif visitors == 8:
        points = 1

    # Update participants points
    cur.execute('UPDATE Participants SET Points = (SELECT Points FROM Participants WHERE Name == "'+name+'")+'+str(points)+'  WHERE Name == "'+name+'"')

    # Update visited counter
    cur.execute('UPDATE Zips SET Visitors = '+str(visitors)+' WHERE Zip == "'+str(zipcode)+'"')

    
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
    latest_epoch=cur.fetchone()

    if latest_epoch is None:
        latest_epoch = float(1438372800)
    else:
        latest_epoch=latest_epoch[0]
        
    ############################
    #     FACEBOOK STUFF       #
    ############################
    # First visit https://developers.facebook.com/tools/explorer for an one hour token
    # See http://stackoverflow.com/questions/12168452/long-lasting-fb-access-token-for-server-to-pull-fb-page-info#
    token=str(np.loadtxt('token.txt',dtype=np.str))

    # August 1th in epoch 1438372800
    facebookurl = 'https://graph.facebook.com/1630748980524187/feed?fields=full_picture,message,from,id,link,created_time&date_format=U&access_token='+token+'&since='+str(latest_epoch)+'&limit=1000'

#    facebookurl = 'https://graph.facebook.com/1630748980524187/feed?fields=full_picture,message,from,id,link,created_time&date_format=U&access_token='+token+'&since=1439644593&limit=100&until=1439649894'
    
    print("Fetching data from Facebook after "+datetime.datetime.fromtimestamp(float(latest_epoch)).strftime('%Y-%m-%d %H:%M:%S'))
    
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
    #  INSERT INTO TMP TABLE   #
    ############################
    # Create TMP Database
    cur.execute("CREATE TABLE tmp(Participant TEXT, Drank_on INT, City TEXT, Zipcode INT, Image TEXT, Link TEXT, Lat FLOAT, Lon FLOAT, Beer TEXT, CONSTRAINT unq UNIQUE (Participant, zipcode))")
    con.commit()

    for post in data['data']:
        if ('message' in post) and ('full_picture' in post):
            entry = ParseFacebook(post)

            if entry is not None:
                # Check for new participants
                cur.execute('SELECT * FROM Participants WHERE Name = "'+entry[0]+'";')
                if cur.fetchone() is None:
                    print("Found new participant.. "+entry[0]+".. Adding to DB!")
                    UpdateUserDatabase(cur,entry[0])

                # Commit beer entry to database
                UpdateBeerDatabase(cur,entry)
                con.commit()
    
    ############################
    #      UPDATE TABLE        #
    ############################
    try:
        cur.execute("INSERT OR REPLACE INTO Beers SELECT * FROM tmp ORDER BY Drank_on ASC")
    except Exception, e:
        print("Failed to in insert new data!")
        print(e)
       	cur.execute("DROP TABLE tmp")
        con.commit()
        exit()

    # THIS IS NOW HANDLED BY THE EXTERNAL SCRIPT
    # Give out points
#    cur.execute("SELECT * FROM tmp ORDER BY Drank_on ASC")
#    for reg in cur.fetchall():
#        UpdatePoints(cur,reg)

    
    ############################
    #      WRITE MAP DATA      #
    ############################
    # Get data for zipcode
    cur.execute('SELECT * FROM tmp;')
    if len(data['data']) > 0 or True:
	participants = cur.fetchall()
    else:
	participants = []

    for p in participants:
        cur.execute('SELECT * FROM Beers WHERE Participant = "'+p[0]+'";')
        s = WriteHeader(p[0].encode('ascii','ignore'));

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

        with open('/home/pi/davfs/maps/latest/latest/exp_'+(p[0].replace(' ','')).encode('ascii','ignore').replace('.','')+'.js','w') as f:
            f.write(s.encode('utf-8'))

    # Write a combined user
    cur.execute('SELECT * FROM Beers GROUP BY Zipcode ORDER BY Drank_on DESC;')
    beers = cur.fetchall()
    s = WriteHeader('AlleDeltagere');

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

    with open('/home/pi/davfs/maps/latest/latest/exp_AlleDeltagere.js','w') as f:
        f.write(s.encode('utf-8'))

    # Write participants to map
    cur.execute('SELECT * FROM Participants ORDER BY Points DESC;')
    participants = cur.fetchall()
    participants.append((None,u'Alle Deltagere',None,None,None))
    print(participants)
    WriteMap(participants)

cur.execute("DROP TABLE tmp")
con.commit()

'''
 COMPUTE STATISTICS
'''

# Compute participant stats
cur.execute("SELECT Participant,count(),100*count()/593.0,(julianday('2020-08-01')-julianday('now'))/(593.0-count()) FROM Beers GROUP BY Participant ORDER BY count() DESC")

stats = pd.DataFrame(cur.fetchall())
stats.columns = ["Navn","Postnumre","Dækning antal (%)","DPP*"]


# Compute area visited
cur.execute("SELECT 100*sum(Zips.area)/43034.83994881 FROM Beers INNER JOIN Zips ON Beers.Zipcode=Zips.zip GROUP BY Beers.Participant ORDER BY count() DESC")
area = stats.insert(2,'Area',[f[0] for f in cur.fetchall()])

# Fetch beers the last 7 days - Old Green Jersy
day7_epoch = (datetime.datetime.now()-datetime.timedelta(days=7)).strftime('%s')
cur.execute("SELECT Participant,count() FROM Beers WHERE Drank_on >= "+day7_epoch+" GROUP BY Participant")
rate=pd.DataFrame(cur.fetchall())
print(rate)
rate.columns = ["Navn","Sidste 7 Dage"]
stats=pd.merge(stats,rate,on="Navn",how="outer")

cur.execute("SELECT Name, First, Points FROM Participants")
rate=pd.DataFrame(cur.fetchall())
rate.columns = ["Navn","FIP","Points"]
stats=pd.merge(stats,rate,on="Navn",how="outer")

stats.columns = ["Navn","Postnumre","Area","Dækning antal (%)","DPP","Sidste 7 dage","FIP","Points"]

# Make a copy of stats to remove rows in
stats_tmp = stats.copy(deep=True)

# Distribute the yellow jersy and remove the player
yellow=(stats_tmp.sort(["Postnumre","Points"],ascending=False))["Navn"].iloc[0]
stats_tmp = stats_tmp[stats_tmp["Navn"] != yellow]

# Distribute the green jersy and remove the player
green=(stats_tmp.sort(["FIP","Points"],ascending=False))["Navn"].iloc[0]
stats_tmp = stats_tmp[stats_tmp["Navn"] != green]

# Check if the jersy is only a loan
green_true=(stats.sort(["FIP","Points"],ascending=False))["Navn"].iloc[0]
if (green != green_true):
    green=green+" <br>("+green_true+")"

# Distribute the polka jersy and remove the player
polka=(stats_tmp.sort(["Area","Points"],ascending=False))["Navn"].iloc[0]
stats_tmp = stats_tmp[stats_tmp["Navn"] != polka]

# Check if the jersy is only a loan
polka_true=(stats.sort(["Area","Points"],ascending=False))["Navn"].iloc[0]
if (polka != polka_true):
    polka=polka+" <br>("+polka_true+")"

# Giveout red shirt and fix duplets
red=(stats_tmp.sort(["Sidste 7 dage","Points"],ascending=False))["Navn"].iloc[0]
stats_tmp = stats_tmp[stats_tmp["Navn"] != red]

# Check if the jersy is only a loan
red_true=(stats.sort(["Sidste 7 dage","Points"],ascending=False))["Navn"].iloc[0]
if (red != red_true):
    red=red+" <br>("+red_true+")"

print('Yellow: '+yellow.encode('utf-8'))
print('Green: '+green.encode('utf-8'))
print('Polkadot: '+polka.encode('utf-8'))
print('Red: '+red.encode('utf-8')+'\n\n')

stats.columns = ["Navn","Postnumre","Dækning Areal (%)","Dækning antal (%)","DPP","Sidste 7 dage","FIP","Points"]

# '''+datetime.datetime.now().strftime("%Y-%m-%d %H:%M").encode('utf-8')+''
s=u'''<link rel="stylesheet" type="text/css" href="table.css">
 <table align="center" class="jersy">
  <thead>
    <tr width="75%">
      <th>Føre</th>
      <th>Sprinter</th>
      <th>Areal</th>
      <th>7 Dages Sprinter</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><img width="150px" height="120px" src="yellow.png"></img></td>
      <td><img width="150px" height="120px" src="green.png"></img></td>
      <td><img width="150px" height="120px" src="polkadot.png"></img></td>
      <td><img width="150px" height="120px" src="red.png"></img></td>
    </tr>
    <tr>
      <td>'''+yellow+'''</td>
      <td>'''+green+'''</td>
      <td>'''+polka+'''</td>
      <td>'''+red+'''</td>
    </tr>
  </tbody>
 </table>
</br>
</br> <h3 align="center">Sidste opdatering: '''+datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S').decode('unicode-escape')+'''</h3> </br>
'''

stats['Navn'] = stats['Navn'].apply(lambda x: '<a target="_parent" href="parti/%s_table.html">%s</a>' % ((x.replace(' ','')).encode('ascii','ignore').replace('.',''),x))
s+=stats.to_html(index=False,classes=["scoreboard"],escape=False)


with open("/home/pi/davfs/table.html", "w") as text_file:
    text_file.write(s.encode('utf-8'))


'''

Print out a score table for each participant

'''
cur.execute("SELECT * FROM Participants")
for par in cur.fetchall():
    s=u'''<html>
    <head>
    <meta charset="utf-8" />
    <link rel="stylesheet" type="text/css" href="../table.css">
    </head>
     <body>
    <h2 align="center">'''+par[1]+'''</h2>
     <table align="center" class="user_stat">
      <thead>
        <tr width="75%">
        <td>Navn</td>
        <td>'''+par[1]+'''</td>
        </tr>
          <td>Points</td>
          <td>'''+str(par[3])+'''</td>
        </tr>
          <td>FIP</td>
          <td>'''+str(par[4])+'''</td>
        </tr>
      </thead>
     </table>
    </br>
    </br>
    </br>

    <h2>Registered</h2>
     <table align="center" class="user_list">
      <thead>
        <tr width="75%">
          <th>Dato</th>
          <th>Postnumre</th>
        </tr>
      </thead>
      <tbody>
          '''
    # Loop over all beers for each participant
    cur.execute("SELECT * FROM Beers WHERE Participant = '"+par[1]+"' ORDER BY Drank_on DESC")
    for b in cur.fetchall():
          s+='<tr><td>'+datetime.datetime.fromtimestamp(float(b[1])).strftime('%Y-%m-%d %H:%M:%S')+'</td>\n<td><a href="'+b[5]+'">'+str(b[3])+", "+b[2]+'</a></td>\n</tr>'
          
    s+= u'''
      </tbody>
     </table>
    </br>
    </br>
    </br>

    '''

    s += u'''
     <h2>Først i følgende postnumre</h2>
     <table align="center" class="zip_list">
      <thead>
        <tr width="75%">
          <th>Postnumre</th>
          <th>Antal besøg i postnumre</th>
        </tr>
      </thead>
      <tbody>
        '''
    # Loop over all beers for each participant
    cur.execute("SELECT name, zip, Visitors FROM Zips WHERE First_Name = '"+par[1]+"' ORDER BY zip DESC")
    for b in cur.fetchall():
          s+= u'<tr><td>'+str(b[1])+'</td>\n<td>'+str(b[2])+'</td>\n</tr>'
#          print(b[0].encode('utf-8'))
          
    s+= u'''
      </tbody>
     </table>
    </body>
    </html>

    '''

    sn = (par[1].replace(' ','')).encode('ascii','ignore').replace('.','')
    print(sn)
    with open("/home/pi/davfs/parti/"+sn+"_table.html", "w") as text_file:
        text_file.write(s.encode('utf-8'))

con.close()

print("DONE!")
