import matplotlib.pyplot as plt
import matplotlib.ticker as tk
from pandas.plotting import table 
import numpy as np
import pandas as pd
import os
import math
from PIL import Image
from pyproj import Transformer
import cv2
import sys

import datatypes as dt
import utilities as utils
import generateBaseImages as baseIm

import warnings
from shapely.errors import ShapelyDeprecationWarning
warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)  


##################################################
# Collection of functions for geo data processing
# Author: Tobias Ranft & Kimberly Mason
# Date: 2022-08-27
##################################################

""" def setPixelValue(pixpos,numberPixel,pixels,value):
    if(pixpos[0]>0 and pixpos[1]>0 and pixpos[0]<numberPixel[0] and pixpos[1]<numberPixel[1]):
        pixels[pixpos[0],pixpos[1]]=value
    else:
        print("pixel outside") """
        
def sweepToImage(pixpos,angle,index):
    angle=angle+math.pi
    cos=math.cos(-angle)
    sin=math.sin(-angle)
    x_s=index*cos
    y_s=index*sin
    posRot=np.add((x_s,y_s),pixpos)
    #return posRot
    return (int(posRot[0]),int(posRot[1]))
    
# Return a colour, if enough colours are non zero (black)
# colourVect[in] vector of colours in
# return colour to use
def returnNonZeroColour(colourVect):
    returnColour=(0,0,0,0)
    counter=0
    for colour in colourVect:
        if(colour[0]>0 or colour[1]>0 or colour[2]>0):
            returnColour=colour
            counter=counter+1
    if(counter<3):
        returnColour=(0,0,0,0)
    return returnColour
        
# When the images get georeferenced there are sometimes small holes.
# I don't know where they are coming from. Since actually with
# the drawing function the should not be holes.
# However this functions closes them with the colour values around
# img[in,out] image to process    
def closeHoles(img):
    width = img.shape[1]
    height = img.shape[0]
    
    	
    grayImage = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    (thresh, bwImg) = cv2.threshold(grayImage, 0, 255, cv2.THRESH_BINARY)
    bwImg=(bwImg/255).astype(np.byte)

    print("closing holes")
    numberOfRows=width/10
    rowCounter=0
    rowPrintProgress=0

    #imgOut=img.copy()
    for j in range(1,width-1,1):
        for i in range(1,height-1,1):
            if(bwImg[i,j]==0):
                counter=bwImg[i+1,j]+bwImg[i-1,j]+bwImg[i,j+1]+bwImg[i,j-1]
                #if(counter>0):
                   # print(str(counter)+" "+str(bwImg[i+1,j])+" "+str(bwImg[i-1,j])+" "+str(bwImg[i,j+1])+" "+str(bwImg[i,j-1]))
                if(counter>2):
                    #print("close hole")
                    pos1=img[i+1,j]
                    pos2=img[i-1,j]
                    pos3=img[i,j+1]
                    pos4=img[i,j-1]
                    outColour=returnNonZeroColour([pos1,pos2,pos3,pos4])
                    img[i,j]=outColour
        if(j>rowCounter):
            rowCounter=rowCounter+numberOfRows
            print(str(rowPrintProgress)+"%")
            rowPrintProgress+=10
    return img
                
    
# Georeference side scan sonar data. So called mosaic.
# coord[in]       Coordinate window which should be processed    
# pathToData[in]  Path to image csv files
# pathToImg[in]   Path to single depth level folder
# pathToMeta[in]  Path to meta data
# cmap[in]        Colour map 
def mosaic(coord,pathToData,pathToImg,pathToMeta,cmap):
    print("Mosaic processing")
    
    # get the meta information
    metaInfo=utils.readMetaInformation(pathToMeta)
    # we want to transfer from global coordinate system WGS84 = epsg4326
    # to a local one that needs to be adapted based on where you are
    # for hamburg that is epsg25832
    # get the local geo coordinate system based on one point in the data
    print(max(metaInfo.sideLat))
    print(min(metaInfo.sideLat))
    print(max(metaInfo.sideLon))
    print(min(metaInfo.sideLon))
    Geocord=dt.Geocord(max(metaInfo.sideLat),min(metaInfo.sideLat),max(metaInfo.sideLon),min(metaInfo.sideLon))
    localCoordSystem=utils.getLocalGeoCoordinateSystem(Geocord)
    
    print("Use local geo coordinate system: "+str(localCoordSystem))
    transformer = Transformer.from_crs("epsg:4326", localCoordSystem)
    #image border
    bottomleft=transformer.transform(coord.south,coord.west)
    topright=transformer.transform(coord.north,coord.east)
    distance=np.subtract(topright,bottomleft)
    print("distance "+ str(distance))
    pixelSize=(coord.pixelSizeMeters,coord.pixelSizeMeters)
    numberPixel=np.divide(distance,pixelSize)
    numberPixel=(int(numberPixel[0]),int(numberPixel[1]))
    print("number pixels "+str(numberPixel))
    maxPixel=pow(2,16)
    if(numberPixel[0]>maxPixel or numberPixel[1]>maxPixel):
        sys.exit("Error too many pixels. Reduce area or resolution") 
        
    #get all files to process
    allFiles=utils.sorted_alphanumeric(os.listdir(pathToData))
        
    #create an empty image    
    cvImage = np.zeros((numberPixel[1],numberPixel[0],4), np.uint8)
        

    #create images and generate property list
    
    propertyList=baseIm.generateImagesAndPropertyList(allFiles,pathToData,pathToImg,cmap)
    for oneProp in propertyList:
        indices=range(oneProp.startIndex,oneProp.startIndex+oneProp.frames,1)
        pixInWidth=int(oneProp.maxRange/pixelSize[1])
        #open image
        imgPath=pathToImg+"/fig_"+oneProp.name+".png"
        img=Image.open(imgPath)
        newsize=(oneProp.frames,pixInWidth*2)
        img=img.resize(newsize)
        pixelsInputImg = img.load()
                
        prevPixPosList=[]
        firstRound=True
        
        for index in indices:
            #print("index "+str(index))
            globalCoord=transformer.transform(metaInfo.sideLat[index],metaInfo.sideLon[index])
            localCoord=np.subtract(globalCoord,bottomleft)
            #print("local cord "+str(localCoord))
            pixpos=(int(localCoord[0]/pixelSize[0]),int(localCoord[1]/pixelSize[1]))
            heading=metaInfo.sideHeading[index]
            imgInX=index-oneProp.startIndex
            #print("heading " +str(heading))
            pixPosList=[]
            pixValList=[]
 
            for onePixel in range(-pixInWidth,pixInWidth,1):
                pixInImage=sweepToImage(pixpos,heading,onePixel)
                pixPosList.append(pixInImage)
               
                imgInY=onePixel+pixInWidth
                #print("img in coord "+str(imgInX)+"  "+str(imgInY))
                value=pixelsInputImg[imgInX,imgInY]
                pixValList.append(value)
            if(not firstRound):
                for i in range(0,(pixInWidth-1),1):
                    pos1=pixPosList[i]
                    pos2=pixPosList[i+1]
                    pos3=prevPixPosList[i]
                    pos4=prevPixPosList[i+1]
                    area = np.array( [pos1, pos2, pos3, pos4] )
                    pixval=pixValList[i+1]
                    pixvalWithAlpha=(pixval[0],pixval[1],pixval[2],255)
                    cv2.drawContours(cvImage, [area], 0,pixvalWithAlpha , -1)
                      
                for i in range((pixInWidth-1),2*(pixInWidth-1),1):
                    pos1=pixPosList[i]
                    #print("pos1 " +str(pos1))
                    pos2=pixPosList[i+1]
                    pos3=prevPixPosList[i]
                    pos4=prevPixPosList[i+1]
                    area = np.array( [pos1, pos2, pos3, pos4] )
                    pixval=pixValList[i+1]
                    pixvalWithAlpha=(pixval[0],pixval[1],pixval[2],255)
                    cv2.drawContours(cvImage, [area], 0, pixvalWithAlpha, -1)

            firstRound=False
            prevPixPosList=pixPosList.copy()
    # close holes in the image
    cvImage=closeHoles(cvImage)
    # flip image
    cvImage=cv2.flip(cvImage, 0)
    # save image
    outPath=os.path.dirname(pathToData)+"/MosaicCV.png"
    cv2.imwrite(outPath, cvImage) 
    # convert image to geotif
    utils.convertToGeoTif(outPath,coord)