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

    <title>Custom Icons Tutorial - Leaflet</title>

    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <link rel="shortcut icon" type="image/x-icon" href="docs/images/favicon.ico" />

    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.1.0/dist/leaflet.css" integrity="sha512-wcw6ts8Anuw10Mzh9Ytw4pylW8+NAD4ch3lqm9lzAsTxg0GFeJgoAtxuCLREZSC5lUXdVyo/7yfsqFjQ4S+aKw==" crossorigin=""/>
    <script src="https://unpkg.com/leaflet@1.1.0/dist/leaflet.js" integrity="sha512-mNqn2Wg7tSToJhvHcqfzLMU6J4mkOImSPTxVZAdo+lcPlk+GhZmYgACEe0x35K7YzW1zJ7XyJV/TT1MrdXvMcA==" crossorigin=""></script>


    <style>
      #map {
      width: 100vw;
      height: 100vh;
      }
    </style>


  </head>
  <body>

    <div id='map'></div>
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
      var map = L.map('map').fitBounds([[53.7465326518,7.56974247323],[57.8457433581,15.0093935068]]);

      map.createPane('labels');

      // This pane is above markers but below popups
      map.getPane('labels').style.zIndex = 650;

      // Layers in this pane are non-interactive and do not obscure mouse/touch events
      map.getPane('labels').style.pointerEvents = 'none';


      var cartodbAttribution = '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="http://cartodb.com/attributions">CartoDB</a>';

      var positron = L.tileLayer('http://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}.png', {
      attribution: cartodbAttribution
      }).addTo(map);

      var positronLabels = L.tileLayer('http://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}.png', {
      attribution: cartodbAttribution,
      pane: 'labels'
      }).addTo(map);

function getColor(d) {
    return d > 6 ? '#800026' :
           d > 5  ? '#BD0026' :
           d > 4  ? '#E31A1C' :
           d > 3  ? '#FC4E2A' :
           d > 2   ? '#FD8D3C' :
           d > 1   ? '#FEB24C' :
           d > 0   ? '#FED976' :
                      '#FFEDA0';
}

      exp_JyllandJSON = L.geoJson(exp_Jylland).addTo(map);
      exp_FynJSON = L.geoJson(exp_Fyn).addTo(map);
      exp_SjaellandJSON = L.geoJson(exp_Sjaelland).addTo(map);

      exp_JyllandJSON.eachLayer(function (layer) {
    var popupContent = '<table><tr><td>' + String(layer.feature.properties['Postnummer']) + ' ' + String(layer.feature.properties['By']) + '</td></tr></table>';
    layer.bindPopup(popupContent);
      });

      exp_FynJSON.eachLayer(function (layer) {
    var popupContent = '<table><tr><td>' + String(layer.feature.properties['Postnummer']) + ' ' + String(layer.feature.properties['By']) + '</td></tr></table>';
      layer.bindPopup(popupContent);
      });

      exp_SjaellandJSON.eachLayer(function (layer) {
    var popupContent = '<table><tr><td>' + String(layer.feature.properties['Postnummer']) + ' ' + String(layer.feature.properties['By']) + '</td></tr></table>';
//      layer.bindPopup(layer.feature.properties.Postnummer);
      layer.bindPopup(popupContent);
      });

    function pop_Postnumre(feature, layer) {					
    var popupContent = '<table><tr><th scope="row">Postnummer</th><td>' + String(feature.properties['POSTNR_TXT']) + '</td></tr><tr><th scope="row">Navn</th><td>' + String(feature.properties['POSTBYNAVN']) + '</td></tr></table>';
            layer.bindPopup(popupContent);
    }

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
    var popupContent = '<table><tr><th scope="row">Navn</th><td>' + String(feature.properties['Navn']) + '</td></tr><tr><th scope="row">Postnummer</th><td>' + String(feature.properties['Postnummer']) + '</td></tr><tr><th scope="row">By</th><td>' + String(feature.properties['By']) + '</td></tr><tr><th scope="row">Dato</th><td>' + String(feature.properties['Dato']) + '</td></tr></table>';
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
    //layerOrder[layerOrder.length] = exp_'''+shortname+'''JSON;
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


    '''
    
    s += '''

//    feature_group.addTo(map);
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
//    var baseMaps = {
//    'Thunderforest Outdoors': basemap_0
//    };
    var baseMaps = {
    'Kort': positron
    };
//    L.control.layers(baseMaps, {'Jylland':Jylland, 'Fyn':Fyn, 'Sjaelland':Sjaelland, 'Thue':exp_ThueSylvesterBordingJSON}).addTo(map);

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
    //L.control.scale({options: {position: 'bottomleft',maxWidth: 100,metric: true,imperial: false,updateWhenIdle: false}}).addTo(map);
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

    with open('/home/christian/davfs/maps/latest/index.html','w') as f:
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
def WritePolygon(data,place,besogende=0):
#
    s = ""

    s += '''{ "type": "Feature", "properties": {"Navn":"'''+data[0]
    s += '''","Postnummer":"'''+str(data[3])
    s += '''","By":"'''+data[2]
    s += '''","Besogende":"'''+str(besogende)
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

        arr = np.array([np.fromstring(x[:-4],dtype=np.float,sep=',') for x in pol.split(' ')])
        s+=np.array2string(arr[:-1],separator=',').replace('\n','').replace(' ','')

        # Write comma if multiple polygons
        if len(poly)-1 == i:
            # Support for MultiGeometry
            if hasattr(place,"MultiGeometry"):
                s=s+''']] } }'''
            else:
                s=s+'''] } }'''
        else:
            s=s+''' ], [ '''

#    except:
#        print("Failed to parse record!")
#        print(data)
#        print(place)

    return s;

'''
This function writes the ende of file
'''
def WriteFooter():
    return '\n]\n}'
