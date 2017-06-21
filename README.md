# pdr-script

Postnummer Danmark Rundt (PDR) is a Danish drinking game where you have to drink a beer in all Danish zip codes (postnummer).

This repo is a collection of scripts to parse the PDR facebook page and maintain the current score of the game. The scripts generate a static HTML page and a client-side leaflet map to show the spatial drunkenness of each participant. It is unfortunately highly tailored to the current infrastructure and would be difficult to deploy else where.

A live demo of the game is available here: www.fredborg-braedstrup.dk/PDR 

# Usage
* Become admin on the facebook page
* Get a facebook access token: https://developers.facebook.com/tools/explorer?method=GET&path=me%3Ffields%3Did%2Cname
* Run the script without any commandline arguments
* Upload the file to my google maps

# Requires
* pykml - pip install pykml
* libxml - sudo apt-get install python-lxml
* pandas
* numpy
