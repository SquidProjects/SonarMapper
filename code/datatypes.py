import sys
import configparser
import os

##################################################
# This file contains the used datatype classes
# Author: Tobias Ranft & Kimberly Mason
# Date: 2022-08-27
##################################################

# Property of one image segment
# segment is a part of an image with constant height
class dataProperties:
    def __init__(self):
        self.minRange=0
        self.maxRange=0
        self.pixelY=0
        self.frames=0
        self.name=""
        self.startIndex=0
        
# properties to assemble several zoom segments 
# to one image
class assembleProperties:
    def __init__(self):
        self.maxDept=0
        self.minDept=100000
        self.finestRes=1000
        self.framesTotal=0
        self.yMax=0
        
# Selection of properties to control the settings 
# of the script. 
class processingSelection:
    def __init__(self):
        # process down scan
        self.down=False
        # process side scan
        self.side=False
        # process primary scan
        self.prime=False
        # process secondary scan
        self.second=False
        # generate georeference
        self.georef=False
        # generate map of the track
        self.track=False
        # correct the coordinates
        self.coordCorr=False
        #call R
        self.callR=False
        
        
        self.cmapDown="self"
        self.cmapSide="self"
        # colour map for the primary chanel
        # https://matplotlib.org/stable/tutorials/colors/colormaps.html
        self.cmapPrime="jet"
        # dept where the image gets cut of
        self.cutOffDept=1000
        
        self.basepath=""
        self.files=[]
        
# Class to hold meta information to the image
class MetaInformation:
    def __init__(self):
        self.dataPrim=[]
        self.dataDown=[]
        self.dataSide=[]
        self.sideLon=[]
        self.sideLat=[]
        self.sideHeading=[]
        
# class to hold information about the requested georeference area
class Geocord:
    def __init__(self,north,south,east,west):
        if(north<south):
            sys.exit("north must be bigger than south") 
        if(east<west):
            sys.exit("east must be bigger than west") 
        self.north=north
        self.south=south
        self.east=east
        self.west=west
        self.pixelSizeMeters=0.5


# reads the config from a config file
def readConfig(pathToConfig):
    if(not os.path.exists(pathToConfig)):
        sys.exit("Cofig file doesn't exist") 
    selection=processingSelection()

    config = configparser.ConfigParser()
    config.read(pathToConfig)

    selection.down = bool(config['views']['downScan']=="True")
    selection.side = bool(config['views']['sideScan']=="True")
    selection.prime = bool(config['views']['primary']=="True")
    selection.second = bool(config['views']['secondary']=="True")
    selection.georef = bool(config['views']['georeference']=="True")
    selection.track = bool(config['views']['plotTrack']=="True")
    
    selection.callR = bool(config['preprocessing']['callIt']=="True")

    selection.coordCorr = bool(config['settings']['coordinateCorrection']=="True")
    selection.cmapPrime = config['settings']['colourMap']
    selection.cutOffDept=int(config['settings']['maxDept'])

    selection.basepath = config['files']['basepath']
    selection.files=config['files']['files'].replace('.','').split(',')

    north = float(config['settingsGeoreference']['north'])
    south = float(config['settingsGeoreference']['south'])
    east = float(config['settingsGeoreference']['east'])
    west = float(config['settingsGeoreference']['west'])
    geo=Geocord(north,south,east,west)
    geo.pixelSizeMeters = float(config['settingsGeoreference']['pixelSizeMeters'])
    return selection, geo