# pdr-script

This collection of scripts parse the PDR facebook page producing a kml file. This file is easy to import into google maps or any GIS software.

# Usage
* Become admin on the facebook page
* Get a facebook access token: https://developers.facebook.com/tools/explorer?method=GET&path=me%3Ffields%3Did%2Cname
* Run the script without any commandline arguments
* Upload the file to my google maps

# Requires
pykml - pip install pykml
libxml - sudo apt-get install python-lxml
pandas
numpy
