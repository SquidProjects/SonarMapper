import os
import cv2
import keras
import numpy as np
import matplotlib.pyplot as plt
import albumentations as A
from tensorflow.keras.callbacks import TensorBoard
import tensorflow as tf
import segmentation_models as sm
import math

# define colours for the different classes
fishCol=(0,255,0)
vegbigCol=(255,100,0)
vegsmallCol= (0,255,255)
groundCol= (0,0,255)
backgroundCol=(100,2,2)

# image patch size: size of the patches which get analyzed
patch_size = (500,500)
# the patch size the model is trained on
model_patch_size = (320, 320)


def generateColourOverlayThreshold(mask):
    """
    Generates an overlay mask where the classes are coloured
    A threshold is used to determine colouration
    """
    # split the mask into its layes, representing the different classes
    background=mask[..., 0].squeeze()
    ground=mask[..., 1].squeeze()
    vegsmall=mask[..., 2].squeeze()
    vegbig=mask[..., 3].squeeze()
    fish=mask[..., 4].squeeze()

    threshold=0.2

    mask_dim = mask.shape
    overlay = np.zeros((model_patch_size[0],model_patch_size[1],3), np.uint8)
    overlay.fill(0)
    overlay[np.where(background>0.5)] = backgroundCol
    overlay[np.where(ground>threshold)] = groundCol
    overlay[np.where(vegsmall>threshold)] = vegsmallCol
    overlay[np.where(vegbig>threshold)] = vegbigCol
    overlay[np.where(fish>threshold)] = fishCol
    overlay= cv2.resize(overlay, patch_size, interpolation = cv2.INTER_AREA)
    return overlay



def generateColourOverlayMax(mask):
    """
    Generates an overlay mask where the classes are coloured
    The maximal class value is used to determine colouration
    """
    # split the mask into its layes, representing the different classes
    background=mask[..., 0].squeeze()
    ground=mask[..., 1].squeeze()
    vegsmall=mask[..., 2].squeeze()
    vegbig=mask[..., 3].squeeze()
    fish=mask[..., 4].squeeze()

    cv2.imwrite("background.jpg", background)
    cv2.imwrite("ground.jpg", ground)
    cv2.imwrite("vegsmall.jpg", vegsmall)
    cv2.imwrite("vegbig.jpg", vegbig)
    cv2.imwrite("fish.jpg", fish)

    threshold=0.2

    mask_dim = mask.shape
    overlay = np.zeros((model_patch_size[0],model_patch_size[1],3), np.uint8)
    overlay.fill(0)

    # for each class create a list array where it has the highes value
    listOfMaks=[background,ground,vegsmall,vegbig,fish]
    def compareMasks(currentMask, pos):
        if(pos<len(listOfMaks)):
            return np.logical_and(np.greater_equal(currentMask, listOfMaks[pos]), compareMasks(currentMask, pos+1))
        else:
            return np.ones((model_patch_size[0],model_patch_size[1]))
    backgroundBiggest=compareMasks(background,0)
    groundBiggest=compareMasks(ground,0)
    vegsmallBiggest=compareMasks(vegsmall,0)
    vegbigBiggest=compareMasks(vegbig,0)
    fishBiggest=compareMasks(fish,0)

    # colour the areas of the highest value with the corresponding colour
    overlay[backgroundBiggest] = backgroundCol
    overlay[groundBiggest] = groundCol
    overlay[vegsmallBiggest] = vegsmallCol
    overlay[vegbigBiggest] = vegbigCol
    overlay[fishBiggest] = fishCol

    overlay= cv2.resize(overlay, patch_size, interpolation = cv2.INTER_AREA)
    return overlay

def extract_background_mask(mask):
    """
    Extracts the background mask for background supression
    """
    background=mask[..., 0].squeeze()
    background= cv2.resize(background, patch_size, interpolation = cv2.INTER_AREA)
    overlay = np.expand_dims(background, axis=2)
    return overlay

def preprocess(imageRaw,preprocessingFu):
    image= cv2.resize(imageRaw, model_patch_size, interpolation = cv2.INTER_AREA)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    sample = preprocessingFu(image=image)
    image = sample['image']
    image = np.expand_dims(image, axis=0)
    return image

def get_preprocessing(preprocessing_fn):   
    _transform = [
        A.Lambda(image=preprocessing_fn),
    ]
    return A.Compose(_transform)

def tileImage(imgPath: str, model, preprocess_input):
    """
    This function reads the image, cuts it into tiles, prepares these tiles
    feeds them into the segmentation network and creates a class based coloured 
    overlay
    """
    # check if image path exsists
    if(not os.path.isfile(imgPath)):
        print("path to image does not exsit. I will quit the programm")
        print(imgPath)
        exit()
    tilesize = patch_size[0]
    img = cv2.imread(imgPath)
    initialImageShape = img.shape
    # pad the image to be cut into equal tiles
    newShape = [0,0]
    newShape[0] = math.ceil((initialImageShape[0]/tilesize)+1)*tilesize
    newShape[1] = math.ceil((initialImageShape[1]/tilesize)+1)*tilesize
    imgOrig = np.zeros((newShape[0],newShape[1],3), np.uint8)
    imgOrig[0:initialImageShape[0],0:initialImageShape[1],0:3] = img.copy()

    # coloured overlay visualizing classes
    label_overlay = np.zeros((newShape[0],newShape[1],3), np.uint8)
    # maks of the background
    background_mask = np.zeros((newShape[0],newShape[1],1), np.float32)

    # loop over the image, cut it in tiles, predict each tile (segmentation) and 
    # assemble the predicted tiles back to a full image
    h, w = newShape
    for i in range(0,w-tilesize,tilesize):
        for j in range(0,h-tilesize,tilesize):
            # get a tile
            cropped_image = imgOrig[j:j+tilesize, i:i+tilesize]
            # preprocess the image
            imgPre=preprocess(cropped_image,get_preprocessing(preprocess_input))
            # feed it into the network and predict the output
            mask=model.predict(imgPre)
            # generate the coloured overlay
            overlay=generateColourOverlayMax(mask)
            label_overlay[j:j+tilesize, i:i+tilesize]=overlay
            # extract the background mask
            background_mask[j:j+tilesize, i:i+tilesize]=extract_background_mask(mask)
    return imgOrig, label_overlay, background_mask

def printLegend(image):
    """
    Function to print the colour legend on the image
    """
    start=(0,0)
    boxWidth=100

    image = cv2.rectangle(image, start, (start[0]+5*boxWidth,start[1]+5*boxWidth), (255,255,255), -1)

    boxStart=start
    boxEnd=(boxStart[0]+boxWidth,boxStart[1]+boxWidth)
    print(boxStart)
    print(boxEnd)
    image = cv2.rectangle(image, boxStart, boxEnd, fishCol, -1)
    image = cv2.putText(image, 'fish', (int(boxStart[0]+boxWidth*1.2),int(boxStart[1]+boxWidth*0.7)), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,0), 2, cv2.LINE_AA)

    boxStart=(0,boxEnd[1])
    boxEnd=(boxStart[0]+boxWidth,boxStart[1]+boxWidth)
    print(boxStart)
    print(boxEnd)
    image = cv2.rectangle(image, boxStart, boxEnd, vegbigCol, -1)
    image = cv2.putText(image, 'vegSmall', (int(boxStart[0]+boxWidth*1.2),int(boxStart[1]+boxWidth*0.7)), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,0), 2, cv2.LINE_AA)

    boxStart=(0,boxEnd[1])
    boxEnd=(boxStart[0]+boxWidth,boxStart[1]+boxWidth)
    image = cv2.rectangle(image, boxStart, boxEnd, vegsmallCol, -1)
    image = cv2.putText(image, 'vegBig', (int(boxStart[0]+boxWidth*1.2),int(boxStart[1]+boxWidth*0.7)), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,0), 2, cv2.LINE_AA)

    boxStart=(0,boxEnd[1])
    boxEnd=(boxStart[0]+boxWidth,boxStart[1]+boxWidth)
    image = cv2.rectangle(image, boxStart, boxEnd, groundCol, -1)
    image = cv2.putText(image, 'Ground', (int(boxStart[0]+boxWidth*1.2),int(boxStart[1]+boxWidth*0.7)), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,0), 2, cv2.LINE_AA)

    boxStart=(0,boxEnd[1])
    boxEnd=(boxStart[0]+boxWidth,boxStart[1]+boxWidth)
    image = cv2.rectangle(image, boxStart, boxEnd, backgroundCol, -1)
    image = cv2.putText(image, 'Background', (int(boxStart[0]+boxWidth*1.2),int(boxStart[1]+boxWidth*0.7)), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,0), 2, cv2.LINE_AA)
    return image

def softenBackgroundMask(maskOverlay):
    """
    This function does not remove the background completly since this would hide a mistake the segmentation made
    but instead it blurrs and darkens the background.
    """
    # close holes in mask background
    kernel = np.ones((5,5),np.float32)
    maskOverlay=cv2.morphologyEx(maskOverlay, cv2.MORPH_CLOSE, kernel)
    maskOverlay = np.expand_dims(maskOverlay, axis=2)

    # The mask gets fluffed to make the transition smooth
    fluffyMask=1.0-maskOverlay
    # loop over the transparency gradient and degrade the corners
    for i in np.arange(0.9,0.1,-0.1):
        kernel = np.ones((5,5),np.float32)
        maskOverlayNew = cv2.erode(maskOverlay,kernel,iterations = 1)
        maskOverlayNew = np.expand_dims(maskOverlayNew, axis=2)
        diff=(maskOverlay-maskOverlayNew)*i

        fluffyMask=cv2.max(fluffyMask,diff)
        maskOverlay=maskOverlayNew

    return np.expand_dims(fluffyMask, axis=2)

def createModel(pathToModel: str):
    """
    Sets up the model. The model needs to match the way it was trained, so
    don't change this parameters here.

    Args:
        pathToModel (str): path where the model is located in the file system
    """
    # define the classes
    CLASSES = ['background', 'ground', 'vegsmall', 'vegbig', 'fish']
    # set the backbone
    BACKBONE = 'efficientnetb3'
    # model name
    modelName = 'seg3.h5'
    preprocess_input = sm.get_preprocessing(BACKBONE)
    # load best weights
    n_classes = 1 if len(CLASSES) == 1 else (len(CLASSES) + 1) 
    activation = 'sigmoid' if n_classes == 1 else 'softmax'
    model = sm.Unet(BACKBONE, classes=n_classes, activation=activation)
    model.load_weights(pathToModel + "/" + modelName) 

    return model, preprocess_input


def segmentImage(imgInPath: str):
    """
    Main method of image segmentation

    Args:
        imgInPath (str): path to the location of the CombinedImageNL image
    """
    print("AI based image segmentation")
    # create the model and the image preprocessing function
    pathToModel = "models"
    model, preprocessing_fu = createModel(pathToModel)
    # predict the image in tiles and reassemble them
    imgOrig, imgLabel, maskOverlay = tileImage(imgInPath + "/CombinedImageNL.jpg" , model, preprocessing_fu)

    # create a background mask with softend corners
    softBackgroundMask=softenBackgroundMask(maskOverlay)
    
    # overlay the labels on the grayscaled image
    gray = cv2.cvtColor(imgOrig, cv2.COLOR_BGR2GRAY)
    gray = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    addedImg = cv2.addWeighted(gray, 0.7, imgLabel, 0.3, 0.0)
    addedImg=printLegend(addedImg)
    cv2.imwrite(imgInPath+"/Segmented.jpg", addedImg) 

    # mask out backround
    blurredBackground=cv2.blur(imgOrig,(19,19))
    blueBackground = np.zeros(imgOrig.shape, np.uint8)
    blueBackground[:]=(100,2,2)
    mixedBackground=cv2.addWeighted(blueBackground, 0.7, blurredBackground, 0.3, 0.0)
    imgCleaned=(imgOrig*softBackgroundMask+mixedBackground*(1-softBackgroundMask)).astype(np.uint8)
    cv2.imwrite(imgInPath+"/Cleaned.jpg", imgCleaned)

    # add labels to cleaned image
    gray = cv2.cvtColor(imgCleaned, cv2.COLOR_BGR2GRAY)
    imgCleanedGray = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
    addedImgClean = cv2.addWeighted(imgCleanedGray, 0.7, imgLabel, 0.3, 0.0)
    addedImgClean=printLegend(addedImgClean)
    cv2.imwrite(imgInPath+"/CleanedSeg.jpg", addedImgClean)    
