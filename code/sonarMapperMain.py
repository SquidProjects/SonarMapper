# -*- coding: utf-8 -*-

import datatypes as dt
import georef
import assembleImages
import utilities as utils
from pathlib import Path
import sys
import os



pathToR='"C:/Program Files/R/R-4.2.1/bin/x64/Rscript.exe"'
# pathToR='Rscript' #for Ubuntu


    
################### Main #####################
    
# get path from command line argument
pathToConfig=sys.argv[1]
# set path in source code
# pathToConfig="PATH/config.ini"  #if you want to run it from the editor you can set the path to the config here

selection,coord= dt.readConfig(pathToConfig)

#callR
if(selection.callR):
    os.system(pathToR+" sonaR.R "+pathToConfig)

for file in selection.files:
    print("######################################")
    print("######################################")
    print("process file "+file)
    print("######################################")
    print("######################################")
    
    pathToTripFolder=selection.basepath+"/"+file

    pathToDown=pathToTripFolder+"/Downscan"
    pathToDownIm=pathToTripFolder+"/downImages"
        
    pathToSide=pathToTripFolder+"/Sidescan"
    pathToSideIm=pathToTripFolder+"/sideImages"
        
    pathToPrim=pathToTripFolder+"/Primary"
    pathToPrimIm=pathToTripFolder+"/primImages"
        
    pathToSecond=pathToTripFolder+"/Secondary"
    pathToSecondIm=pathToTripFolder+"/downSecond"
        
    metaPath=pathToTripFolder+"/sl.csv"
    if(selection.coordCorr):
        utils.fixPosition(metaPath,2)
        metaPath=pathToTripFolder+"/slEdited.csv"
    
    if(selection.down):
        print("##### process downScan ########")
        Path(pathToDownIm).mkdir(parents=True, exist_ok=True)
        assembleImages.processOneView(pathToDown,pathToDownIm,side=False,cmap=selection.cmapDown,cutOffDept=selection.cutOffDept)
        
    if(selection.side):
        print("##### process sideScan ########")
        Path(pathToSideIm).mkdir(parents=True, exist_ok=True)
        assembleImages.processOneView(pathToSide,pathToSideIm,side=True,cmap=selection.cmapSide,cutOffDept=1000)
    
    if(selection.prime):
        print("##### process primeScan ########")
        Path(pathToPrimIm).mkdir(parents=True, exist_ok=True)
        assembleImages.processOneView(pathToPrim,pathToPrimIm,side=False,cmap=selection.cmapPrime,cutOffDept=selection.cutOffDept)
    
    if(selection.second):
        print("##### process secondScan ########")
        Path(pathToSecondIm).mkdir(parents=True, exist_ok=True)
        assembleImages.processOneView(pathToSecond,pathToSecondIm,side=False,cmap=selection.cmapPrime)
        
    if(selection.georef):
        #if necesary produce side view
        Path(pathToSideIm).mkdir(parents=True, exist_ok=True)
        assembleImages.processOneView(pathToSide,pathToSideIm,side=True,cmap=selection.cmapSide,cutOffDept=1000)
        # produce mosaic
        georef.mosaic(coord,pathToSide,pathToSideIm,metaPath,cmap=selection.cmapSide)
        
    if(selection.track):
        utils.plotTrackWithDept(metaPath)


print("##### done ###########")





