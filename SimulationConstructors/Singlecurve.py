## Libraries
import math
from os import error
from pathlib import Path
import imageio.v3 as iio
import cv2
#from numpy.ma.timer_comparison import cur
import skimage
from skimage import morphology
import numpy as np
import matplotlib.pyplot as plt
from scipy import ndimage
from skimage.morphology import disk, opening, skeletonize
from skimage.transform import probabilistic_hough_line


def extractCurves(ima):
    #Read the image
    #ima = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    #image = ndimage.gaussian_filter(img, sigma=1.0)
    
    plt.figure(figsize=(10,6))
    plt.imshow(ima, cmap='gray')
    plt.show()
    image = ndimage.gaussian_filter(ima, sigma=1)
    #Threshold the image
    _, binary = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY_INV)  # Make curves white
    plt.figure(figsize=(10,6))
    plt.imshow(binary, cmap='gray')
    plt.show()
    # Step 3: Skeletonize the binary image
    dilated = cv2.dilate(binary, kernel=np.ones((3,3), np.uint8), iterations=1)
    #skeleton = morphology.skeletonize(dilated // 255, method= 'lee')  # Normalize binary to 0 and 1
    skeleton = morphology.thin(dilated)
    skeleton = (skeleton * 255).astype("uint8")  # Convert back to 8-bit for OpenCV

    #skeleton = ndimage.gaussian_filter(skeleto, sigma=1.0)
    plt.figure(figsize=(10,6))
    plt.imshow(skeleton, cmap='gray')
    plt.show()
    
    def is_endpoint(skeleton, x, y):
        # Count the number of neighbors (8-connectivity)
        neighbors = np.sum(skeleton[y-1:y+2, x-1:x+2] == 255) - 1 # Subtract 1 to exclude the pixel itself
        return neighbors == 1  # Exactly 1 neighbor indicates an endpoint
    # Step 4: Identify intersection points
    def is_intersection(skeleton, x, y):
        neighbors = np.sum(skeleton[y-1:y+2, x-1:x+2] == 255)-1
        return neighbors > 2  # More than 2 neighbors means it's an intersection

    height, width = skeleton.shape
    print(height)
    print(width)
    endtemp = []
    intersection_points = []   
    for y in range(0, height):
        for x in range(0, width):
            if skeleton[y,x] == 255 and is_endpoint(skeleton, x, y):
                endtemp.append((x,y))
            if skeleton[y, x] == 255 and is_intersection(skeleton, x, y):
                intersection_points.append((x, y))

    endpoints = sorted(endtemp, key=lambda point: point[0])
    #endpoints = sorted_points
    #Split the sorted array into two arrays
    #mid_index = len(sorted_points) // 2
    #startpoints = sorted_points[:mid_index]  # First half
    #endpoints = sorted_points[mid_index:]  # Second half   
    print(intersection_points)
    #print(startpoints)
    print(endpoints)
    #print(sorted_points)
    
    if len(intersection_points) > 0:
        min_x = (min(point[0] for point in intersection_points) - 1)
        max_x = (max(point[0] for point in intersection_points) + 1)
    else:
        min_x = 0
        max_x = 0
    # Iterate over the selected x-coordinates
    def profileline(x):
        
        binary_points = []
        
        # Ensure x is within image bounds
        if 0 <= x < skeleton.shape[1]:
            # Loop over all y-coordinates in the column
            for y in range(skeleton.shape[0]):
                if skeleton[y, x] == 255:  # Binary point (white in binary image)
                    binary_points.append((x, y))  # Append the (x, y) position
       
        result = []
        for i in range(len(binary_points)):
            # Checks if there's a previous point with same x value, and if it is +1
            if i > 0 and binary_points[i][1] == binary_points[i - 1][1] + 1:
                # Pop the previous point
                result.pop()  
            # Add the current point to the result
            result.append(binary_points[i])
        print(f"Binary points: {binary_points}")
        print(f"Final Binary points: {result}")
        return result
    intersectstart = profileline(min_x)
    intersectend = profileline(max_x)

    def checkslope(point1, point2):
        x = point2[0]-point1[0]
        if x == 0:
            return 0.0
        return (point2[1]-point1[1])/x
    
    def interpolate(x, point1, point2):
        x1 = point1[0]
        y1 = point1[1]
        x2 = point2[0]
        y2 = point2[1]

        if x < x1 or x > x2:
            raise ValueError("x is out of bounds!")
        # Calculate the interpolated y-value
        return y1 + (y2 - y1) * (x - x1) / (x2 - x1)

    def col_round(x):
        frac = x - math.floor(x)
        if frac < 0.5: return math.floor(x)
        return math.ceil(x)
    # Refined trace function to handle intersections
    def trace_curve_with_gradients(skeleton, start_x, start_y, intersection_start, intesection_end):
        curve = [(start_x, start_y)]
        visited = set(curve)
        current_x, current_y = start_x, start_y
        localmaximaormin = (start_x,start_y)
        currenttempslope = 999
        counter = 0
        while True:
            neighbors = []
            counter = counter+1
            #(10,10) range(9, 12) (9,9) (9,10) (9,11)
            for ny in range(max(0, current_y-1), min(skeleton.shape[0], current_y + 2)):
                for nx in range(max(0, current_x), min(skeleton.shape[1], current_x + 2)):
                    
                    if (nx, ny) != (current_x, current_y) and skeleton[ny, nx] == 255 and (nx, ny) not in visited:
                        neighbors.append((nx, ny))
                #grad = (ny - current_y) / (nx - current_x + 1e-6)
                        
            
            if not neighbors:
                if len(endpoints) == 1 or len(endpoints) == 0:
                    endpoints.pop()
                    break
                
                tempsave = 0
                temppoint = (current_x, current_y)
                for i in range(len(endpoints)):
                    if temppoint == endpoints[i]:
                        tempsave = i

                for j in range(tempsave,len(endpoints)):
                    tempendpoint = endpoints[j]
                    
                    if tempendpoint[0] > current_x:
                        numofpoints = tempendpoint[0] - current_x
                        for i in range(1,numofpoints):
                            tempx = current_x+i
                            ytemp = col_round(interpolate(tempx, temppoint, tempendpoint))
                            for ny in range(max(0, ytemp-1), min(skeleton.shape[0], ytemp + 2)):
                                for nx in range(max(0, tempx), min(skeleton.shape[1], tempx + 2)):
                                    
                                    if (nx, ny) != (current_x, current_y) and skeleton[ny, nx] == 255 and (nx, ny) not in visited:
                                        visited.add((nx, ny))
                            visited.add((tempx, ytemp))
                            curve.append((tempx, ytemp))   
                        current_x = tempendpoint[0]
                        current_y = tempendpoint[1]
                        endpoints.remove(endpoints[j])  
                        break
                endpoints.remove(endpoints[tempsave])
                for ny in range(max(0, current_y-1), min(skeleton.shape[0], current_y + 2)):
                    for nx in range(max(0, current_x), min(skeleton.shape[1], current_x + 2)):
                        
                        if (nx, ny) != (current_x, current_y) and skeleton[ny, nx] == 255 and (nx, ny) not in visited:
                            neighbors.append((nx, ny))
                if len(neighbors) == 0:
                    break
                """     endpoints.pop(point)
                else:
                    print("error, exit")
                    break """

            counter = counter + 1
            tempslope = checkslope((current_x,current_y), neighbors[0])
            if (tempslope != 0.0):
                if currenttempslope == 999:
                    currenttempslope = tempslope
                if (currenttempslope > 0 and tempslope > 0):
                    currenttempslope = tempslope
                if (currenttempslope < 0 and tempslope < 0):
                    currenttempslope = tempslope
                if (currenttempslope > 0 and tempslope < 0):
                    localmaximaormin = (current_x,current_y)
                    currenttempslope = tempslope
                    counter = 0
                    print(localmaximaormin)
                if (currenttempslope < 0 and tempslope > 0):
                    localmaximaormin = (current_x,current_y)
                    currenttempslope = tempslope
                    counter = 0
                    print(localmaximaormin)
            
            current_x, current_y = neighbors[0]  

            if (current_x,current_y) in intersection_start:
                visited.add((current_x, current_y))
                curve.append((current_x, current_y))
                bestslope = 999999.9
                tempindex = 0
                point = (current_x,current_y)
                #tempstart = curve[0]
                curvejumpback = 10
                if counter < curvejumpback:
                    grad = checkslope(localmaximaormin,point)
                else:
                    grad = checkslope(curve[-curvejumpback],point)

                for i in range(0,len(intesection_end)):     
                    slope = checkslope(point, intesection_end[i])
                    compare = abs(grad-slope)
                    if compare < bestslope:
                        bestslope = compare
                        tempindex = i
                endpoint = intesection_end[tempindex] 
                numofpoints = endpoint[0] - point[0]
                for i in range(1,numofpoints):
                    tempx = current_x+i
                    ytemp = col_round(interpolate(tempx, point, endpoint))
                    for ny in range(max(0, ytemp-1), min(skeleton.shape[0], ytemp + 2)):
                        for nx in range(max(0, tempx), min(skeleton.shape[1], tempx + 2)):
                            
                            if (nx, ny) != (current_x, current_y) and skeleton[ny, nx] == 255 and (nx, ny) not in visited:
                                visited.add((nx, ny))
                    visited.add((tempx, ytemp))
                    curve.append((tempx, ytemp))

                current_x = endpoint[0]
                current_y = endpoint[1]  
                visited.add((current_x, current_y))
                curve.append((current_x, current_y))
            else:
                visited.add((current_x, current_y))
                curve.append((current_x, current_y))

        return curve

    curves = []

    for x, y in endpoints: #+ intersection_points:
        curve = trace_curve_with_gradients(skeleton, x, y, intersectstart, intersectend)
        curves.append(curve)

    # Plot curve helper function
    def plot_curve(curve, title):
        x_coords, y_coords = zip(*curve)
        fig, ax = plt.subplots(figsize=(10,5))
        ax.set_xlim(0.0, width)
        ax.set_ylim(0.0, height)
        #plt.figure(figsize=(10, 5))
        ax.plot(x_coords, y_coords, 'b-')
        plt.title(title)
        plt.gca().invert_yaxis()  # Match image coordinates
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.show()
    for i, curve in enumerate(curves):
        plot_curve(curve, f"Curve {i + 1}")
    return curves
    


xtemp = 0
ytemp = 12000
wtemp = 1250

testFile = "SimulationConstructors/simplecurve.tif"
#image = cv2.imread(testFile)
#image = cv2.imread(testFile, cv2.IMREAD_GRAYSCALE)
""" cv2.imwrite("testfolder/scantest.png", img) """
image = cv2.imread(testFile, cv2.IMREAD_GRAYSCALE)
h,w = image.shape
#Choose the region of interest including excat boundries the graph
rx, ry, rw, rh = 0,0, w, h
#rx,ry,rw,rh = cv2.selectROI('Select The Complete and Exact Boundaries of Graph',image)
#graph = image#[ry:ry+rh,rx:rx+rw]
#cv2.destroyWindow('Select The Complete and Exact Boundaries of Graph')

#tempgraph = process_chunks(image.copy())

#Enter the min and max values from the source graph here
y_min,y_max = 0.0, 100.0 
x_min,x_max = 10629.75, 10655.75

#Extract the curve points on the image
#image_path = "path_to_your_image.png"
curves = extractCurves(image)

#iio.imwrite("Testresults/plot.tif",curvenum)
#Map curve (x,y) pixel points to actual data points from graph
curve_normalized1 = [[np.float64((cx/rw)*(x_max-x_min)+x_min),np.float64((1-cy/rh)*(y_max-y_min)+y_min)] for cx,cy in curves[0]]
curve_normalized1 = np.array(curve_normalized1)
print(curve_normalized1)
#Lasiotester
#Plot the simulatedcurve
fig, ax = plt.subplots(figsize=(10,5))
ax.set_xlim(10629.75, 10655.75)
ax.set_ylim(0.0, 100.0)
ax.plot(curve_normalized1[:,0],curve_normalized1[:,1],'o-',linewidth=3)
ax.grid(True)
plt.show()



#lasfn = "../T14502Las/T14502_02-Feb-07_JewelryLog.las"
lasfn = "T14502Las/T14502_02-Feb-07_JewelryLog.las"
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

print(metadata)
print(units)
depth = las['DEPT']
#y = np.flip(depth,0)
tempGAMM = las['GAMM']
x = 0
x = np.array(depth[100:350])
y = np.array(tempGAMM[100:350]) 

for i in range(len(y)):
     if y[i] > 100:
          y[i] -= 100

interpolating = 50
y2 = y[:105]
x2 = x[:105]


temparraycurve1 = np.zeros((len(x2),2))
for i in range(len(x2)):
    temparraycurve1[i] = (x2[i], y2[i])

testdatacurve1 = np.array(temparraycurve1)

from scipy.interpolate import interp1d
from sklearn.metrics import mean_squared_error, mean_absolute_error

#Filter for NAN
testfiltered = testdatacurve1[~np.isnan(testdatacurve1).any(axis=1)]
# Extract x and y from test and real
x_sim, y_sim = curve_normalized1[:, 0], curve_normalized1[:, 1]
x_real, y_real = testfiltered[:, 0], testfiltered[:, 1]

# Interpolate real values
interpolator = interp1d(x_real, y_real, kind='linear', fill_value="extrapolate")
#Interpolate sim
y_real_interp = interpolator(x_sim)

#Mean Square and mean absolute
mse = mean_squared_error(y_sim, y_real_interp)
mae = mean_absolute_error(y_sim, y_real_interp)

print("mean squared error:", mse)
print("Mean absolute error:", mae)

#circularx = x % threshold
""" print(xreverse[0])
print(xreverse[:-1]) """
""" fig, ax = plt.subplots(figsize=(5,3))
#ax.plot(xreverse, yreverse, color='red', linewidth=1)
ax.set_xlim(10629.75, 10655.75)
ax.set_ylim(0, 100)
ax.plot(x1,y1,color='blue', linewidth=1)
 """