#!/usr/bin/env python3
#
# Uitslagen bekijken zonder gedoe met de app of traag lodende site?
#
# Dit script:
# 1. Download uitslagen van de staatsloterij en schrijft ze naar
#    individuele files in uitslagen/*.json
# 2. Laadt de loten.json met een array te checken loten
# 3. Print uitslag naar scherm
#
# LET OP: Loten worden tegen de uitslag gecheckt alsof je met
# alle spellen meedoet. Het kan dus zijn dat de uitslag teveel
# belooft.
#
# Aan de geprinte uitslagen kunnen geen rechten worden geleend.
# Gewonnen? Check het zelf nog even bij de staatsloterij.
#

from pathlib import Path
import urllib.request
import re
import time
import json
import os

uitslagdir = "uitslagen"

def cleanhtml(raw_html):
    striptag = re.compile(r'<.*?>')
    stripchars = re.compile(r'&.*?;')
    cleantext = re.sub(striptag, '', raw_html)
    cleantext = re.sub(stripchars, '', cleantext).strip()
    return cleantext.strip()


def gettrekkingen():
    filename = uitslagdir + "/nieuwste-trekking.html"

    if oldfile(filename):
        urllib.request.urlretrieve(
            "https://staatsloterij.nederlandseloterij.nl/trekkingsuitslag", filename)

    trekkingen = []
    with open(filename) as xml_file:
        for line in xml_file:
            if line.__contains__("/trekkingsuitslag/"):
                start = 0+line.index('"/trekkingsuitslag/') + \
                    ("/trekkingsuitslag/".__len__())+1
                end = 0+line.index('" ', start)
                trekkingen.append(line[start:end])
    return trekkingen


def oldfile(filename):
    return not Path(filename).is_file() or (Path(filename).stat().st_mtime < (time.time()-60*60))


def getuitslag(trekking):
    # Download uitslag to xml
    filenamexml = uitslagdir + '/' + trekking+".xml"
    filenamejson = uitslagdir + '/' + trekking+".json"
    if oldfile(filenamejson):
        # print('File '+filename+' birthtime '+str(Path(filename).stat().st_mtime)+' is before '+str(time.time()-1440))
        urllib.request.urlretrieve(
            "https://staatsloterij.nederlandseloterij.nl/trekkingsuitslag/" + trekking, filenamexml)

        # Parse uitslag from xml
        uitslag = {}
        with open(filenamexml) as xml_file:
            for line in xml_file:
                if line.__contains__('class="ticket-letters"'):
                    lot = cleanhtml(str(line))
                    #print('lotnummer '+lot)
                if line.__contains__('class="full-amount ticket-prize"'):
                    prijs = cleanhtml(str(line))
                    #print('    prijs '+ prijs)
                if line.__contains__('class="fraction-amount ticket-prize"'):
                    kleineprijs = cleanhtml(str(line))
                    #print('1/5 prijs '+kleineprijs)
                    uitslag[lot] = prijs

        # Write uitslag to json
        with open(filenamejson, 'w') as json_file:
            json.dump(uitslag, json_file, indent=2)

        # Remove temporary xml file
        os.remove(filenamexml)
    else:
        with open(filenamejson, 'r') as json_file:
            uitslag = json.load(json_file)

    # Return uitslag as dict
    return uitslag


def getprijzen(uitslag, mijnlot):
    prijzen = []
    for lot in uitslag:
        if re.match(lot, mijnlot):
            prijzen.append("Gewonnen met "+mijnlot +
                           ": "+uitslag[lot]+" ("+lot+")")
    return prijzen


if __name__ == "__main__":
    print("================== Staatsloterij uitslag ===================== ")
    lotenfile = "loten.json"
    if Path(lotenfile).is_file():
        with open(lotenfile, 'r') as json_file:
            loten = json.load(json_file)
    else:
        print("LET OP: TESTLOTEN")
        with open("testloten.json", 'r') as json_file:
            loten = json.load(json_file)

    # Create uitslagen directory
    Path(uitslagdir).mkdir(parents=True, exist_ok=True)
    
    for trekking in gettrekkingen():
        uitslag = getuitslag(trekking)
        for mijnlot in loten:
            prijzen = getprijzen(uitslag, mijnlot)
            if prijzen:
                for prijs in prijzen:
                    print(trekking.ljust(25, ' ')+prijs)
            else:
                print(trekking.ljust(25, ' ')+"Geen prijs.")
