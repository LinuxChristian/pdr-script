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

from pdr.maputils import *

# Turn off pandas column width limitor
#if int((pd.version.short_version).split('.')[1]) >= 11:
pd.set_option('display.max_colwidth', -1)
#else:
#	pd.set_printoptions('display.max_colwidth', -1)



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
            return None
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
        if ('message' in post) and ('full_picture' in post) and post['created_time'] > latest_epoch:
            entry = ParseFacebook(post)

            if entry is not None:
                # Check for new participants
                cur.execute('SELECT * FROM Participants WHERE Name = "'+entry[0]+'";')
                if cur.fetchone() is None:
#                    print("Found new participant.. "+entry[0]+".. Adding to DB!")
                    UpdateUserDatabase(cur,entry[0])

                # Commit beer entry to database
                UpdateBeerDatabase(cur,entry)
                con.commit()
            else:
                # Post a comment that message was rejected
                url = 'https://graph.facebook.com/{}/comments'.format(post['id'])
                url_data = urllib.urlencode({'access_token':token,
                                         'message':'Din post kunne ikke behandles. Tjek postnummer og by! Skal genposten inden den kan registeres.',
                                         'method':'post'})
                response = urllib2.urlopen(url, url_data)
                print('Unable to parse post. User informed... Status:')
                page = response.read()

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
#    cur.execute('SELECT * FROM tmp;')
    cur.execute('SELECT Name FROM Participants;')
    if len(data['data']) > 0 or True:
	participants = cur.fetchall()
    else:
	participants = []

    print(participants)
    for p in participants:
        cur.execute('SELECT * FROM Beers WHERE Participant = "'+p[0]+'";')
        s = WriteHeader(p[0].encode('ascii','ignore'));

        beers = cur.fetchall()
        for i,b in enumerate(beers):
            try:
                place = PM[PMN.index(str(b[3]))]    
            except Exception, e:
                print(PMN)
                print "Error %s:" % e.args[0]
                sys.exit(1)

            s=s+WritePolygon(b,place)

            if i < len(beers)-1:
                s += ',\n'


        s += WriteFooter()

        print("Writing exp_",p)
        with open('/home/christian/davfs/maps/latest/latest/exp_'+(p[0].replace(' ','')).encode('ascii','ignore').replace('.','')+'.js','w') as f:
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

    with open('/home/christian/davfs/maps/latest/latest/exp_AlleDeltagere.js','w') as f:
        f.write(s.encode('utf-8'))

    # Write participants to map
    cur.execute('SELECT * FROM Participants ORDER BY Points DESC;')
    participants = cur.fetchall()
    participants = [(None,u'Alle Deltagere',None,None,None)] + participants
#    print(participants)
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
#print(rate)
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
if len(stats_tmp["Sidste 7 dage"].dropna()) == 0:
    red = "Ingen! Drik mere!"
else:
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


with open("/home/christian/davfs/table.html", "w") as text_file:
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
    with open("/home/christian/davfs/parti/"+sn+"_table.html", "w") as text_file:
        text_file.write(s.encode('utf-8'))

con.close()

print("DONE!")
