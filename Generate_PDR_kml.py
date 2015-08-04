#!/usr/bin/python
# -*- coding: utf-8 -*-

# Json libs
from pprint import pprint
import json
import urllib,urllib2

# General libs
import datetime
import numpy as np

# KML libs
from pykml import parser
from pykml.factory import KML_ElementMaker as KML
from lxml import etree

# Settings - csv may be buggy
output='kml'

# HEX transparency
trans = "7b"

# Participants: Name, Colour
parti = [[u"Christian Fredborg Brædstrup",trans+"a6cee3"],
         [u"Thue Sylvester Bording",trans+"1f78b4"],
         [u"Toke Højbjerg Søltoft",trans+"b2df8a"],
         [u"Daniel Søndergaard Skov",trans+"33a02c"],
         [u"Niels Emil Søe",trans+"fb9a99"],
         [u"Kenni Dinesen Petersen",trans+"e31a1c"],
         [u"Bo Klinkvort Kempel",trans+"fdbf6f"],
         [u"Rasmus Rumph",trans+"ff7f00"],
         [u"Rasmus Bødker Madsen",trans+"cab2d6"],
         [u"Jonas Møller Pedersen",trans+"6a3d9a"],
         [u"Laust H. Lorentzen",trans+"ffff99"],
         [u"Søren Thesbjerg Andersen",trans+"b15928"],
         [u"Josef Nielsen",trans+"1f78b4"],
         [u"Thomas Holm Nielsen",trans+"1f78b4"],
         [u"Thomas L. Rasmussen",trans+"1f78b4"],
         [u"Rasmus Bording",trans+"1f78b4"],
         [u"Freddy TusindPenge",trans+"1f78b4"]
]

stats = []

# First visit https://developers.facebook.com/tools/explorer for an one hour token
token='CAACEdEose0cBAPhmInGb8yW58ZBuQ0rPFmZBvuW4nVZCi6KBfe8ZCUfRiWds9KZBT9dsykuZBUXgoUW4NnTmKakfh1rVdAmFlITZCzTZBZBWZBC1GQxSTSzIZAGjnTAh37mlvgGhmJUGBQ1EWMsZAuQG7zCU9bJAJAbsolyjbbNxirMRmQ6FE4SPbaLxWVRr5EcWk8usPdA0uvgcNZAYNmZAT4GpfKKzbXrVqXvEUZD'

facebookurl = 'https://graph.facebook.com/1630748980524187/feed?access_token='+token+'&since=1438372800&limit=100&date_format=U'

# Note: Facebook timestamps are local to the device and encoded in Pacific time
# Timestamps are returned in Unix epoch time

print("Fetching data from Facebook")
response = urllib2.urlopen(facebookurl)

# Check for HTTP codes other than 200
if response.code != 200:
    print('Status:', response.code, 'Problem with the request. Exiting.')
    exit()

# Decode the JSON response into a dictionary and use the data
jsondata = response.read()
data = json.loads(jsondata)

if output == 'csv':
    csv = [];

    for post in data['data']:
        if ('picture' in post) and ('message' in post):
            print("Post includes a photo")
            # Convert unix timestamp in seconds
            t = datetime.datetime.fromtimestamp(float(post["created_time"]))
            tt = t.strftime('%Y-%m-%d')
            name = post["from"]["name"].encode('utf-8')
            # Split message on newline
            msg = post["message"].encode('utf-8').split('\n')
            # Get zipcode
            zipcode = msg[0][:4]
            # Get town
            town = msg[0][5:]
            csv.append([tt,name,zipcode,town])

    np.savetxt("/tmp/pdr.csv",csv,delimiter=",",fmt='%s')
elif output == 'kml':

    # Open zipcode kml file
    root = parser.fromstring(open('Danske_postnumre.kml','r').read())
    
    # Get Placemarks
    PM = root.Document.findall("Placemark")
    PMN = root.Document.findall("Placemark/name")

    # Create new empty document
    d = KML.Document(KML.name("Postnr Danmark Rundt"))
    
    for p in parti:
        fld = KML.Folder(KML.name(p[0]))        

        print("Processing "+p[0])
        for post in data['data']:
            if ('picture' in post) and ('www.google.com' not in post['picture']) and ('message' in post):
                if (p[0] in post['from']['name']):
                    t = datetime.datetime.fromtimestamp(float(post["created_time"]))
                    tt = t.strftime('%Y-%m-%d')
                    name = post["from"]["name"].encode('utf-8')

#                    if ("Thue Sylvester Bording" 
                    
                    # Grab GPS if it exists
                    if "place" in post:
                        print("Found GPS data.. haps haps haps")
 #                       fld.append(KML.point(KML.coordinates(
 #                           post["place"]["location"]["longitude"],
 #                           post["place"]["location"]["latitude"])))
                        
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

                    # Get town
                    town = msg[0][5:]

                    place = PM[PMN.index(zipcode)]
                    # Fix a new style
                    place.styleUrl = KML.StyleUrl("#"+p[0].split(' ')[0])
                    # Add a nice comment
                    place.description = KML.description(str(tt))#+"<br> <a href='"+post["picture"]+"'>Foto</a>]]>"

#                    print(p[0]+" Found zip "+str(zipcode))
                    fld.append(place)

        # Append folder to document if any records exist
        if (len(fld.findall('Placemark/')) > 0):
            print("Added "+p[0])
            stats.append([name, len(fld.findall('Placemark/')), len(fld.findall('Placemark/'))/597.0])
            # Create unique style
            ls = d.append(KML.Style(KML.PolyStyle(KML.LineStyle(KML.width("1.5")),KML.color(p[1])),id=p[0].split(' ')[0]))
            d.append(fld)
        else:
            print("No records found")
    # Print xml pretty
    xmlstr=etree.tostring(d, pretty_print=True)
    
    # Write final string
    with open("/tmp/test.kml",'w') as f:
        f.write(xmlstr.encode('utf-8'))


    print(stats)
else:
    print('Output '+output+" not supported!")
    
exit()
