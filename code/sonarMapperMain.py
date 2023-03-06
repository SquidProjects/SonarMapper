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
#pathToConfig=sys.argv[1]
# set path in source code
#pathToConfig="PATH/config.ini"  #if you want to run it from the editor you can set the path to the config here
pathToConfig="C:/Users/EddiH/Downloads/SonarData/git/SonarMapper/example/config.ini"

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

    if(selection.side):
        print("##### process sideScan ########")
        Path(pathToSideIm).mkdir(parents=True, exist_ok=True)
        img, prop=assembleImages.processOneView(pathToSide,pathToSideIm,side=True,cmap=selection.cmapSide,cutOffDept=1000)
        assembleImages.printLegendAndSave(img,prop,pathToSide,side=True,legend=True)
    
    if(selection.down):
        print("##### process downScan ########")
        Path(pathToDownIm).mkdir(parents=True, exist_ok=True)
        img, prop=assembleImages.processOneView(pathToDown,pathToDownIm,side=False,cmap=selection.cmapDown,cutOffDept=selection.cutOffDept)
        assembleImages.printLegendAndSave(img,prop,pathToDown,side=False,legend=True)
    
    if(selection.prime):
        print("##### process primeScan ########")
        Path(pathToPrimIm).mkdir(parents=True, exist_ok=True)
        img, prop=assembleImages.processOneView(pathToPrim,pathToPrimIm,side=False,cmap=selection.cmapPrime,cutOffDept=selection.cutOffDept)
        assembleImages.printLegendAndSave(img,prop,pathToPrim,side=False,legend=True)

    if(selection.combinedDownPrime):
        # get the minimal dept between Down and prime image
        minDepth= assembleImages.getSmallerDepth(pathToDown,pathToPrim)
        minDepth=min(minDepth,selection.cutOffDept)
        #process the prime image again, but this time with a the colour stype of Down to keep it comparable
        pathToPrimeMono=pathToTripFolder+"/PrimaryMonochrome"
        Path(pathToPrimeMono).mkdir(parents=True, exist_ok=True)
        primeImg,_ =assembleImages.processOneView(pathToPrim,pathToPrimeMono,side=False,cmap=selection.cmapDown,cutOffDept=minDepth)
        # process down
        Path(pathToDownIm).mkdir(parents=True, exist_ok=True)
        downImg, prop=assembleImages.processOneView(pathToDown,pathToDownIm,side=False,cmap=selection.cmapDown,cutOffDept=minDepth)
        #combine images
        combinedImg= utils.combineImages(downImg,primeImg)
        assembleImages.printLegendAndSave(utils.openCvToPilImage(combinedImg),prop,pathToPrim,side=False,legend=True,filename="CombinedImage")
        
    if(selection.second):
        print("##### process secondScan ########")
        Path(pathToSecondIm).mkdir(parents=True, exist_ok=True)
        img, prop=assembleImages.processOneView(pathToSecond,pathToSecondIm,side=False,cmap=selection.cmapPrime)
        assembleImages.printLegendAndSave(img,prop,pathToSecond,side=False,legend=True)
        
    if(selection.georef):
        #if necesary produce side view
        Path(pathToSideIm).mkdir(parents=True, exist_ok=True)
        assembleImages.processOneView(pathToSide,pathToSideIm,side=True,cmap=selection.cmapSide,cutOffDept=1000)
        # produce mosaic
        georef.mosaic(coord,pathToSide,pathToSideIm,metaPath,cmap=selection.cmapSide)
        
    if(selection.track):
        utils.plotTrackWithDept(metaPath)


print("##### done ###########")





