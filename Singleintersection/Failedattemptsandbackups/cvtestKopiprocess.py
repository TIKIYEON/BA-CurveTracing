## Libraries

from pathlib import Path
import imageio.v3 as iio
import cv2
import skimage
import numpy as np
import matplotlib.pyplot as plt
from scipy import ndimage
from skimage.morphology import disk, opening, skeletonize, thin

## Read and display the image
#Function to take difference between two consecutive points
now = 0
def differentiator(variable):
    global now
    before = now
    now = variable
    return now-before

#Function to find the intersectionpoints 
def extractIntersectionpoints(src_image):
    # Profile interval
    profile_interval = 5
    h, w, c = src_image.shape

    # Convert image to grayscale and detect edges
    gray = cv2.cvtColor(src_image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 5, 20)

    fig, ax = plt.subplots()
    ax.imshow(edges, cmap= "gray")
    print("plot 1:")
    plt.show()
    # Initialize graph for visualization
    curve_points = []

    # Scan through the width at intervals
    for xi in range(w // profile_interval):
        # Draw profile line on the image
        cv2.line(graph, (xi*profile_interval, 0), (xi*profile_interval, h), (255, 0, 0), 1)

        # Extract intensity profile along the line
        profile = skimage.measure.profile_line(gray, (0, xi*profile_interval), (h, xi*profile_interval),  linewidth=1, mode='constant')

        # Find intersection points
        for y, intensity in enumerate(profile):
            if intensity > 0 and edges[int(y), xi*profile_interval] != 0:  # Validate intersection
                curve_points.append((xi*profile_interval, int(y)))
                cv2.circle(graph, (xi*profile_interval, int(y)), 3, (0, 255, 0), -1)  # Mark point

    # Display final graph
    cv2.imshow('Final Graph with Intersections', graph)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    return curve_points

def Skeletonized(chunk):
    overlays = []
    # Grayscale
    #print(f'i.shape: \n {i.shape[2]}')
    I_gray = skimage.color.rgb2gray(chunk)
    #print(f'i gray.shape: \n {I_gray.shape}')
    I_grayg = ndimage.gaussian_filter(I_gray, sigma=2)
    # Attempt with OTSU's method
    threshold = skimage.filters.threshold_otsu(I_grayg)
    mask = (I_grayg > threshold)
    min_pixels = 200
    row_mask = np.sum(mask, axis=1) < min_pixels
    col_mask = np.sum(mask, axis=0) < min_pixels
    #print(f'row mask: \n {row_mask}')
    # Add a new axis and add the maskings to that as well with np.repeat
    mask_combined = np.repeat((row_mask[:, np.newaxis] | col_mask[np.newaxis, :])[:, :, np.newaxis], chunk.shape[2], axis=2)
    #print(f'mask combined: \n {mask_combined}')
    K = np.maximum(chunk, np.max(chunk) * mask_combined)
    plt.figure(figsize=(10,6))
    plt.imshow(K, cmap='gray')
    plt.show()
    se = disk(10)
    J = skimage.morphology.opening(K.mean(axis=2), se)
    plt.figure(figsize=(10,6))
    plt.imshow(J, cmap='gray')
    plt.show()
    #J_closed = skimage.morphology.closing(J, se)
    S = thin(J<128)
    #plt.figure(figsize=(10,10))
    #plt.subplot(2, 2, 4)
    
    overlay = np.zeros(chunk.shape[:2] + (3,), dtype=np.uint8) + 255
    overlay[S] = [255, 0, 0]
    #plt.imshow(overlay)
    #plt.imshow(i, cmap="gray", alpha=0.2)
    #plt.axis("image")
    print(overlay)
    overlays.append(overlay)
    print(overlays)
    
    plt.imshow(overlay)
    #plt.imshow(i, cmap="gray", alpha=0.2)
    plt.axis("image")
    plt.show()
    #iio.imwrite("Profilelinetes/Skeleton2.tif",overlay)
        
    return overlays

#Read the image
xtemp = 0
ytemp = 12000
wtemp = 1250

#testFile = "Profilelinetes/overlaytest0.tif"
testFile = "C:/Users/willi/OneDrive/Skrivebord/Bachelor/Github/Digitizing-overlapping-curves/Profilelinetest/SimCurve8.tif"
image = cv2.imread(testFile)
""" cv2.imwrite("testfolder/scantest.png", img) """

h,w,c = image.shape
#Choose the region of interest including excat boundries the graph
rx, ry, rw, rh = 0,0, w, h
#rx,ry,rw,rh = cv2.selectROI('Select The Complete and Exact Boundaries of Graph',image)
graph = image#[ry:ry+rh,rx:rx+rw]
#cv2.destroyWindow('Select The Complete and Exact Boundaries of Graph')

tempgraph = Skeletonized(image.copy())

""" #Enter the min and max values from the source graph here
y_min,y_max = 0, 190
x_min,x_max = 10604.7500, 10667.0    

#Extract the curve points on the image
curve = extractIntersectionpoints(graph)

#iio.imwrite("Testresults/plot.tif",curvenum)
#Map curve (x,y) pixel points to actual data points from graph
curve_normalized = [[float((cx/rw)*(x_max-x_min)+x_min),float((1-cy/rh)*(y_max-y_min)+y_min)] for cx,cy in curve]
curve_normalized = np.array(curve_normalized)
print(curve_normalized)

#Plot the simulatedcurve
plt.figure(figsize=(15,7))
plt.plot(curve_normalized[:,0],curve_normalized[:,1],'o-',linewidth=3)
plt.title('Curve Re-Constructed')
plt.grid(True)
plt.show()

#Lasiotester
lasfn = "C:/Users/willi/OneDrive/Skrivebord/Bachelor/Github/Digitizing-overlapping-curves/T14502Las/T14502_02-Feb-07_JewelryLog.las"
#lasfn = "../T14502Las/T14502_02-Feb-07_JewelryLog.las"
#lasfn = "T14502Las/T14502_02-Feb-07_JewelryLog.las"
import lasio
las = lasio.read(str(lasfn),ignore_header_errors=True)
#las = lasio.read(str(lasfn),encoding="cp866")
#las = lasio.read(str(lasfn),encoding="windows-1251")

headers=las.keys()
units = {}
for j in range(0, len(headers)):
     uval = las.curves[j].unit
     units[headers[j]] = uval

dataarr = las.data
metaheaders=las.well.keys()
metadata=[]
metadata.append({})
metadata.append({})
metadata.append({})

for j in range(0, len(metaheaders)):
     uval = las.well[j].unit
     metadata[0][metaheaders[j]] = uval

     tval = las.well[j].value
     metadata[1][metaheaders[j]] = str(tval)

     dval = las.well[j].descr
     metadata[2][metaheaders[j]] = str(dval)

print(units)
depth = las['DEPT']
tempGAMM = las['GAMM']

# Generate sample data with 2700 points
x = np.array(depth[:250])

y = np.array(tempGAMM[:250])
xreverse = x
yreverse = np.flip(y,0)

#Same format for print
temparray = np.zeros((len(xreverse),2))
for i in range(len(xreverse)):
    temparray[i] = (xreverse[i], yreverse[i])

testdata = np.array(temparray)
print(testdata)

from scipy.interpolate import interp1d
from sklearn.metrics import mean_squared_error, mean_absolute_error

#Filter for NAN
testfiltered = testdata[~np.isnan(testdata).any(axis=1)]
# Extract x and y from test and real
x_sim, y_sim = curve_normalized[:, 0], curve_normalized[:, 1]
x_real, y_real = testfiltered[:, 0], testfiltered[:, 1]

# Interpolate real values
interpolator = interp1d(x_real, y_real, kind='linear', fill_value="extrapolate")
#Interpolate sim
y_real_interp = interpolator(x_sim)

#Mean Square and mean absolute
mse = mean_squared_error(y_sim, y_real_interp)
mae = mean_absolute_error(y_sim, y_real_interp)

print(mse)
print(mae) """