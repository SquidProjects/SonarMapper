import matplotlib.pyplot as plt
import pandas as pd
import os
import re
import geopy.distance
import contextily
import rasterio
import sys
import geopandas as gpd
from shapely.geometry import Point
import datatypes as dt
from pyproj import CRS
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info

##################################################
# This file contains helper functions
# Author: Tobias Ranft & Kimberly Mason
# Date: 2022-08-27
##################################################

# Converts a image as png and the coordinate this image covers to a geotif. This is a file with geo information which can be 
# for example be imported to QGIS
# input:
# pathToImage  path to the png image
# coord        coordinates of the image
def convertToGeoTif(pathToImage, coord):    
    dataset = rasterio.open(pathToImage, 'r')
    bands = [1,2,3]
    data = dataset.read(bands)
    transform = rasterio.transform.from_bounds(coord.west, coord.south, coord.east,coord.north, data.shape[1], data.shape[2])
    crs = {'init': 'epsg:4326'}
    
    writePath=os.path.dirname(pathToImage)
    
    _, width, height = data.shape
    with rasterio.open(writePath+"/GeoMosaic.tif", 'w', driver='GTiff',
                       width=width, height=height,
                       count=3, dtype=data.dtype, nodata=0,
                       transform=transform, crs=crs) as dst:
        dst.write(data, indexes=bands)
        
# Function to plot the track on a map and colour by dept
# This function will download the map data from OpenStreetMap and therefore needs internet
# input:
# pathToMeta  path to the file containing the meta data     
def plotTrackWithDept(pathToMeta):
    print("plot track with dept")
    bathy_data = gpd.read_file(pathToMeta, delimiter=',', header=0)

    bathy_data['WaterDepth'] = pd.to_numeric(bathy_data['WaterDepth'])

    bathy_data = bathy_data.loc[~((bathy_data['WaterDepth'] == 0))]

    bathy_data = bathy_data[['SurveyTypeLabel','Latitude','Longitude',
                             'WaterDepth']]

    bathy_data["geometry"] = bathy_data.apply(lambda x:Point(float(x["Longitude"]), 
                                                             float(x["Latitude"])), axis=1)

    geo = gpd.GeoDataFrame(bathy_data, geometry='geometry')

    geo = geo.set_crs(epsg=4326)

    data = geo.to_crs(epsg=3857)

    #fig, ax = plt.subplots(figsize=(14,6)) 
    fig, ax = plt.subplots() 
    data.plot(ax=ax, column='WaterDepth',cmap = 'ocean_r', legend=True, 
              legend_kwds={'label': "Depth (m)"})
    plt.xlabel("Longitude") 
    plt.ylabel("Latitude") 
    bounds = data.total_bounds
    print(bounds)
    dx=abs(bounds[2]-bounds[0])/2
    dy=abs(bounds[3]-bounds[1])/2
    toadd = max(dx,dy)
    ax.set_xlim(bounds[0]-toadd, bounds[2]+toadd)
    ax.set_ylim(bounds[1]-toadd, bounds[3]+toadd)
    
    print("get map from openStreetMap")
    contextily.add_basemap(ax, zoom=16, source=contextily.providers.OpenStreetMap.Mapnik)
    # plt.show()
    outName= os.path.dirname(pathToMeta)+"/TrackWithDept.png"
    plt.savefig(outName, dpi=300)
    
# The positions taken from GNSS are not accurate enough. Meaning there are several frames with the same position.
# This leads to problems when georeferencing it. Therefore it is necessary to stretch them apart
# This is currently done by simply looking for 2 positions that are a measurable distance apart and assigning 
# the position in between linearly.
# This function will create a corrected meta data file
# input:
# filename filepath to meta data
# distance minimal distance between 2 position in meter
def fixPosition(filename,distance):
    print("Fix position")
    outFile=os.path.dirname(filename)+"/slEdited.csv"
    #print("exists "+str(os.path.exists(outFile)))
    if(not os.path.exists(outFile)):
        #print("fix file "+str(filename))
        data = pd.read_csv(filename)
        
        Lat=data["Latitude"].copy()
        Lon=data["Longitude"].copy()
        Type=data["SurveyTypeLabel"]
        Heading=data["GNSSHeading"]
    
        index1=0
        index2=1
        maxIndex=len(Lat)
        
        tenPercent=maxIndex/10
        printCounter=0
        
        maxReached=False
        while(maxReached==False):
            dist=0
            point1=(Lat[index1],Lon[index1])
            while(dist<distance and index2<maxIndex):
                point2=(Lat[index2],Lon[index2])
                dist=geopy.distance.geodesic(point1, point2).m
                index2+=1
            if(index2==maxIndex):
                index2=maxIndex-1
                maxReached=True
            # print("distance "+str(dist))
            # print("index "+str(index2))
            
            startPoint=(Lat[index1],Lon[index1])
            dindex=index2-index1
            dlat=(Lat[index2]-Lat[index1])/dindex
            dlon=(Lon[index2]-Lon[index1])/dindex
                    
            for i in range(0,dindex,1):
                Lat[i+index1]=startPoint[0]+i*dlat
                Lon[i+index1]=startPoint[1]+i*dlon
            index1=index2
            if(index1>printCounter):
                printCounter=printCounter+tenPercent
                print(str(int(printCounter/tenPercent)*10)+"%")
            
        
        newData=pd.DataFrame(Type)
        newData["Latitude"]=Lat
        newData["Longitude"]=Lon
        newData["GNSSHeading"]=Heading
        newData["WaterDepth"]=data["WaterDepth"]
        
        newData.to_csv(outFile)
        print("ende of fix pos")

# Function to read the meta information
# input
# path  path to meta information
def readMetaInformation(path):
    print("Start read meta information")
    data = pd.read_csv(path)
    metaInfo = dt.MetaInformation()
    metaInfo.dataPrim = data[data['SurveyTypeLabel'] == 'Primary']
    metaInfo.dataDown = data[data['SurveyTypeLabel'] == 'Downscan']
    metaInfo.dataSide = data[data['SurveyTypeLabel'] == 'Sidescan']
    metaInfo.sideLat=metaInfo.dataSide.loc[:,"Latitude"].values.tolist()
    metaInfo.sideLon=metaInfo.dataSide.loc[:,"Longitude"].values.tolist()
    metaInfo.sideHeading=metaInfo.dataSide.loc[:,"GNSSHeading"].values.tolist()
    return metaInfo

# Function to sort file name in alpha numeric order
# This is important to process the files in the right order
# input
# data list with the file names
# return list with file names sorted
def sorted_alphanumeric(data):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(data, key=alphanum_key)

# This function takes a position and return a local coordinate system
# which fits
# Geocord geocoordinates
# return local geo coordinate system
def getLocalGeoCoordinateSystem(Geocord):
    utm_crs_list = query_utm_crs_info(
        datum_name="WGS 84",
        area_of_interest=AreaOfInterest(
            west_lon_degree=Geocord.west, 
            south_lat_degree=Geocord.south, 
            east_lon_degree=Geocord.east,
            north_lat_degree=Geocord.north,
        ),
    )
    utm_crs = CRS.from_epsg(utm_crs_list[0].code)
    return utm_crs