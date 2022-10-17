import matplotlib.pyplot as plt
import pandas as pd
import os
import math
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 

# internal libraries
import datatypes as dt

##################################################
# This file generates based on the image csv files png files
# Author: Tobias Ranft & Kimberly Mason
# Date: 2022-08-27
##################################################

# This function extracts the properties of a single image csv file
# data[in]           pandas csv file
# properties[in,out] properties of this file
def fillProperties(data,properties):
    numberOfLines=len(data)
    properties.frames=len(data.columns)-1
    properties.pixelY=numberOfLines-3
    lastCell=data.iloc[numberOfLines-1]["Unnamed: 0"]
    splitCell=lastCell.split(" ")
    properties.minRange=float(splitCell[1])
    properties.maxRange=float(splitCell[2])
    #print(str(properties.frames)+"X"+str(properties.pixelY))
    
# Generates an png image out of an image csv file
# This version of the function uses matplotlib and the colour profile can easily be changed
# However the number of colour gradients must be smaller otherwise it will take for ever
# path[in]       path to the image csv file
# nr[in]         number of the image processed, for naming the saved image
# imgPath[in]    path where the image should be saved 
# cmapString[in] color map
def processOneFrame(path,nr,imgPath,cmapString):
    #print(path)
    data = pd.read_csv(path,header=0, dtype=str)
    
    properties=dt.dataProperties()
    fillProperties(data,properties)
    properties.name=nr
    
    #create image if it does not exits
    image_path=imgPath+"/fig_"+str(nr)+".png"
    if (not os.path.exists(image_path)):
        
        data = data[:-1]
        data = data.drop('Unnamed: 0', axis = 1)
        data = data.dropna()
        data=data.astype(int)
        
        if (len(data.columns)<2):
            data['copy'] = data['V1']
        
        fig, ax = plt.subplots()
        ax = plt.contourf(data,antialiased=True,cmap=cmapString,levels=50)
        plt.axis('off')
        
        
        figure = plt.gcf()
        
        # matplotlib can not be asked to give the image a certain number of pixels. Therefore the ratio and 
        # the dpi values are calculated
        inchesY=10
        dpiVal=math.ceil(properties.pixelY/inchesY)
        #print("dpiVal "+str(dpiVal))
        inchesX=properties.frames/dpiVal
        #print("inchesX "+str(inchesX))
        figure.set_size_inches(inchesX, inchesY)
        plt.savefig(image_path, transparent=False, bbox_inches='tight', pad_inches=0,dpi=dpiVal+100)
        plt.close("all")
    return properties


# Generates an png image out of an image csv file
# This version of the function is an own implementation. It produces an image with exactly the
# right number of pixels and can produce a higher level of details. However the colour map is fix.
# path[in]    path to the image csv file
# nr[in]      number of the image processed, for naming the saved image
# imgPath[in] path where the image should be saved 
def processOneFrameSelf(path,nr,imgPath):
    # print(path)
    data = pd.read_csv(path,header=0, dtype=str)
        
    properties=dt.dataProperties()
    fillProperties(data,properties)
    properties.name=nr
    
    #create image if it does not exits
    image_path=imgPath+"/fig_"+str(nr)+".png"
    if (not os.path.exists(image_path)):
        
        data = data[:-1]
        data = data.drop('Unnamed: 0', axis = 1)
        data = data.dropna()
        data=data.astype(int)
        # convert dataframe to list -> faster access
        dataList=data.values.tolist()
        
        #max value of data list        
        maxYValue=int(max(max(dataList)))
        #print("max "+str(maxYValue))
        
        # create an empty image
        new_im = Image.new('RGB', (properties.frames,properties.pixelY))
        #print("image size "+str(properties.frames)+" "+str(properties.pixelY))
        pixels = new_im.load()
        
        #create value dict for all colour to speed up
        valDict={}
        for i in range(maxYValue+10):
            pixval=int(255/maxYValue*i)
            r=int(pixval/255*78)
            g=int(pixval/255*255)
            b=int(pixval/255*174)
            valDict[i]=(r,g,b)
        #print(valDict)
            
        # loop over the image and transfer the intensities to colour values
        for row in range (0,properties.pixelY,1):
            for col in range (0,properties.frames,1):
                pixval=valDict[dataList[row][col]]
                pixels[col,row]=pixval#(pixval,pixval,pixval)
        new_im=new_im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        new_im.save(image_path, "PNG")
    return properties


# This function will loop over all image csv files and create png image files out of them.
# Moreover it will create a list with the properties of this files
# Already created images will not be recreated
# allFiles[in] list with the names to all files to process
# path[in]     base path of where the image csv files are located
# imgPath[in]  path to where the png image files should be saved
# cmap[in]     colour map that should be used. use "self" for detailed processing
# return: returns a list with the properties of for each image. This list will be as well created if
#         the image are all already present
def generateImagesAndPropertyList(allFiles,path,imgPath,cmap):
    propertyList=[]
    fameCounter=0
    numberImages=len(allFiles)
    imageCounter=1
    for file in allFiles:
        res1=file.find("_")
        res2=file.find(".")
        nr=file[res1+1:res2]
        #print(nr)
        if(cmap=="self"):
            oneProperty=processOneFrameSelf(path+"/"+file,nr,imgPath)
        else:
            oneProperty=processOneFrame(path+"/"+file,nr,imgPath,cmap)
        #set frame counting from start
        oneProperty.startIndex=fameCounter
        fameCounter+=oneProperty.frames
        propertyList.append(oneProperty)
        
        #print progress
        print("processed image "+str(imageCounter) + " out of "+str(numberImages))
        imageCounter=imageCounter+1
    return propertyList

# Labels the image with dept distance lines and numbers
# For Primary,Secondary and Downscan
# image[in,out] image to be labeled
# maxDepth[in]  max dept in meters that the image represents
def drawOnImage(image,maxDepth):
    width, height = image.size
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("arial.ttf", 24)
    # font = ImageFont.truetype("Ubuntu-R.ttf", 24) use this line for ubuntu instead of arial
    
    #draw depth
    deptPerPixel=maxDepth/height
    _10mPixDiff=int(10/deptPerPixel)
    _1mPixDiff=int(1/deptPerPixel)
    #draw depth lines
    PixDiff=_1mPixDiff
    diffInMeters=1
    if(maxDepth>20):
        PixDiff=_10mPixDiff
        diffInMeters=10
    
    currentdepth=0
    for i in range(0,height,PixDiff):
        deptToPrint='%.1f' % currentdepth
        draw.text((0, i),deptToPrint,(255,255,255),font=font)
        draw.line((50, i, width,i), fill=255)
        currentdepth=currentdepth+diffInMeters
        
        
    #draw frames
    for i in range(100,width,100):
        draw.text((i, 0),str(i),(255,255,255),font=font)

# Labels the image with side distance lines and numbers
# For Sidescan
# image[in,out] image to be labeled
# maxDepth[in]  max distance in meters to one side that the image represents        
def drawOnSideImage(image,maxDepth):
    width, height = image.size
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("arial.ttf", 24)
    # font = ImageFont.truetype("Ubuntu-R.ttf", 24) use this line for ubuntu instead of arial
    
    #draw dept
    deptPerPixel=maxDepth*2/height
    _10mPixDiff=int(10/deptPerPixel)
    _1mPixDiff=int(1/deptPerPixel)
    #draw dept lines
    PixDiff=_1mPixDiff
    diffInMeters=1
    if(maxDepth>20):
        PixDiff=_10mPixDiff
        diffInMeters=10
    
    currentdepth=-maxDepth
    #halfHeight=int(height/2)
    for i in range(0,height,PixDiff):
        deptToPrint='%.1f' % currentdepth
        draw.text((0, i),deptToPrint,(255,255,255),font=font)
        draw.line((50, i, width,i), fill=255)
        currentdepth=currentdepth+diffInMeters
        
        
    #draw frames
    for i in range(100,width,100):
        draw.text((i, 0),str(i),(255,255,255),font=font)
