import os
from PIL import Image
# set max image pixel of PIL
Image.MAX_IMAGE_PIXELS = None

import datatypes as dt
import utilities as utils
import generateBaseImages as baseIm
import pandas as pd

import warnings
from shapely.errors import ShapelyDeprecationWarning
warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning) 

##################################################
# This file stitches images of different zoom 
# levels together
# Author: Tobias Ranft & Kimberly Mason
# Date: 2022-08-27
##################################################

# Sets max image sizes. If image is too big, rescaling will happen
maxImageWidth=65000
maxImageHeight=2000

# Crops an image at a certain depth. This is important since sometimes the auto zoom of the
# Fishfinder zooms to for example 80 m for one frame but the actual depth is just 10 m.
# depth[in] depth where cut off should happen
# image[in] image to crop
# maxDepth[in] maximum depth of the file
# returns cropped image        
def cropImageAtDept(depth,image,maxDepth):
    width, height = image.size
    deptPerPixel=maxDepth/height
    pixelToCut=int(depth/deptPerPixel)
    #print("crop at "+str(pixelToCut))
    area = (0, 0, width-5, pixelToCut)
    #area = (0, 0, width, 800)
    imagecrop = image.crop(area)
    return imagecrop

# Generates properties necessary to stitch the images of different zoom levels together
# propertyList[in] list containing the properties of each base image
# returns image assembly properties
def generateAssembleProperties(propertyList):
    #find biggest depth
   assembleProp=dt.assembleProperties()
   for prop in propertyList:
       assembleProp.maxDept=max(assembleProp.maxDept,prop.maxRange)
       assembleProp.minDept=min(assembleProp.minDept,prop.maxRange)
       assembleProp.finestRes=min(assembleProp.finestRes,prop.maxRange/prop.pixelY)
       assembleProp.framesTotal=assembleProp.framesTotal+prop.frames
   #print("max dept "+str(assembleProp.maxDept))
   #print("finest res "+str(assembleProp.finestRes))
   #print("framesTotal "+str(assembleProp.framesTotal))
    # create final image
   assembleProp.yRes=int(assembleProp.maxDept/assembleProp.finestRes)
   return assembleProp

# Function to assemble single images with fixed depth to one big image
# new_im[in,out]    assembled image to be generated from the function
# propertyList[in]  list with properties of all sub images
# assembleProp[in]  information to assemble single images
# side[in]          is it a side scan? Otherwise it is a Downscan or primary     
# pathForImages[in] path to where the singe images are stored
def assembleScan(new_im,propertyList,assembleProp,side:bool,pathForImages):
    new_width, new_height = new_im.size
    new_half_height=new_height/2
    currentFrame=0
    for oneProp in propertyList:
        #print("maxRange "+str(oneProp.maxRange))
        #print("pixy "+str(oneProp.pixelY))
        imgPath=pathForImages+"/fig_"+oneProp.name+".png"
        img=Image.open(imgPath)

        #img=img.transpose(Image.FLIP_TOP_BOTTOM)
        img=img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        
        resizeFactor=oneProp.maxRange/assembleProp.minDept
        #print("resizefaktor "+str(resizeFactor))
        newsize=(oneProp.frames,int(oneProp.pixelY*resizeFactor))
        #img.thumbnail(size)
        img=img.resize(newsize)
        width, height = img.size
        height_half=height/2
        #print("current frame "+str(currentFrame))
        yShift=int(new_half_height-height_half)*side
        new_im.paste(img, (currentFrame,yShift))
        currentFrame=currentFrame+oneProp.frames


# pathToData[in]  path to image csv files
# side[in]        is it a side scan? Otherwise its a Downscan or primary 
# legend[in]      should a legend be added
# filename[in]    part of the name of the image to save
def printLegendAndSave(img, assembleProp,pathToData,side:bool, legend,filename="finalImage"):
    if(legend):
        if(side):
            baseIm.drawOnSideImage(img,assembleProp.maxDept)
        else:
            baseIm.drawOnImage(img,assembleProp.maxDept)
    
    #print("I will save now")
    typeOfImg=os.path.basename(os.path.normpath(pathToData))
    savepath=os.path.dirname(pathToData)
    #print(savepath)
    LegendLabel="L" if legend == True else "NL"
    img.save(savepath+"/"+typeOfImg+filename+LegendLabel+".jpg", "JPEG",quality=90)

# Process one view of the sonar with all its zoom levels. (like a full Downscan or full Sidescan)    
# The final image will be saved one folder above the path to data
# pathToData[in]  path to image csv files
# pathToImg[in]   path to where the singe zoom level images should be stored
# side[in]        is it a side scan? Otherwise its a Downscan or primary 
# cmap[in]        colour map
# cutOffDept[in]  maximum depth in meters to cut the image off
def processOneView(pathToData,pathToImg,side:bool,cmap:str,cutOffDept):
    
    allFiles=utils.sorted_alphanumeric(os.listdir(pathToData))

    #create images
    propertyList=baseIm.generateImagesAndPropertyList(allFiles,pathToData,pathToImg,cmap)
        
    # get assemble properties
    assembleProp=generateAssembleProperties(propertyList)

    # generate empty image
    new_im = Image.new('RGB', (assembleProp.framesTotal,assembleProp.yRes))

    # assemble image
    assembleScan(new_im,propertyList,assembleProp,side,pathToImg)

    if(assembleProp.maxDept>cutOffDept):
        new_im=cropImageAtDept(cutOffDept,new_im,assembleProp.maxDept)
        assembleProp.maxDept=cutOffDept

    size=min(assembleProp.framesTotal,maxImageWidth),min(assembleProp.yRes,maxImageHeight)
    resizedImg=new_im.resize(size)

    return resizedImg, assembleProp

    if(legend):
        if(side):
            baseIm.drawOnSideImage(resizedImg,assembleProp.maxDept)
        else:
            baseIm.drawOnImage(resizedImg,assembleProp.maxDept)
    
    #print("I will save now")
    typeOfImg=os.path.basename(os.path.normpath(pathToData))
    savepath=os.path.dirname(pathToData)
    #print(savepath)
    LegendLabel="L" if legend == True else "NL"
    resizedImg.save(savepath+"/"+typeOfImg+"finalIamge"+LegendLabel+".jpg", "JPEG",quality=90)
    # resizedImg.save(savepath+"/"+typeOfImg+"finalIamge.png", "PNG")

def getSmallerDepth(pathDown,pathPrime):
    
    maxDeptDown=0
    allFiles=utils.sorted_alphanumeric(os.listdir(pathDown))
    for file in allFiles:
        properties=dt.dataProperties()
        data = pd.read_csv(pathDown+"/"+file,header=0, dtype=str)
        baseIm.fillProperties(data,properties)
        maxDeptDown=max(maxDeptDown,properties.maxRange)
    
    maxDeptPrime=0
    allFiles=utils.sorted_alphanumeric(os.listdir(pathPrime))
    for file in allFiles:
        properties=dt.dataProperties()
        data = pd.read_csv(pathPrime+"/"+file,header=0, dtype=str)
        baseIm.fillProperties(data,properties)
        maxDeptPrime=max(maxDeptPrime,properties.maxRange)
        
    
    return min(maxDeptDown,maxDeptPrime)
    
