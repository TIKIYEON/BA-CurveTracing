## Libraries
from doctest import testfile
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
from scipy.ndimage import gaussian_filter1d
from skimage import color, img_as_float
from skimage.morphology import disk, opening, skeletonize, remove_small_objects
from skimage.transform import probabilistic_hough_line
from skimage.measure import label, regionprops
from skimage.filters import gaussian, frangi, hessian, meijering
from skimage.segmentation import active_contour
from scipy.interpolate import interp1d

#from skimage.features import hessian_matrix, hessian_matrix_eigvals

class LinearInterpolator:
    def __init__(self, point1, point2):
        self.x1, self.y1 = point1
        self.x2, self.y2 = point2
        if self.x1 >= self.x2:
            raise ValueError("point1's x-coordinate must be less than point2's x-coordinate")

    def interpolate(self, x):
        if x < self.x1 or x > self.x2:
            raise ValueError("x is out of bounds!")
        return self.y1 + (self.y2 - self.y1) * (x - self.x1) / (self.x2 - self.x1)
    
    @staticmethod
    def col_round(x):
        frac = x - math.floor(x)
        return math.floor(x) if frac < 0.5 else math.ceil(x)

    def interpolate_series(self, start_x):
        num_of_points = self.x2 - start_x
        interpolated_values = []
        for i in range(1, num_of_points):
            temp_x = start_x + i
            temp_y = self.col_round(self.interpolate(temp_x))
            interpolated_values.append((temp_x, temp_y))
        return interpolated_values



""" def detect_ridges(gray, sigma=3.0):
    hxx, hyy, hxy = hessian_matrix(gray, sigma)
    i1, i2 = hessian_matrix_eigvals(hxx, hxy, hyy)
    return i1, i2 """

def extractCurves(ima):
    #Read the image
    #ima = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    #image = ndimage.gaussian_filter(img, sigma=1.0)
    
    plt.figure(figsize=(10,6))
    plt.title("original image")
    plt.imshow(ima, cmap='gray')
    plt.show()
    
    plt.figure(figsize=(10,6))
    plt.imshow(ima, cmap='gray')
    plt.show()
    #image = ndimage.gaussian_filter(ima, sigma=1.0)
    #Threshold the image
    _, binary = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY_INV)  # Make curves white
    """ plt.figure(figsize=(10,6))
    plt.imshow(binary, cmap='gray')
    plt.show()
    #Skeletonize the binary image
    dilated = cv2.dilate(binary, kernel=np.ones((3,3), np.uint8), iterations=1) """
    #skeleton = morphology.skeletonize(dilated // 255, method= 'lee')  # Normalize binary to 0 and 1
    skeleton = morphology.thin(binary)
    skeleton = (skeleton * 255).astype("uint8")  # Convert back to 8-bit for OpenCV

    #skeleton = ndimage.gaussian_filter(skeleto, sigma=1.0)
    
    #skeleton = ndimage.gaussian_filter(skeleto, sigma=1.0)
    plt.figure(figsize=(10,6))
    plt.title("Skeleton image")
    plt.imshow(skeleton, cmap='gray')
    plt.show()

    
    #Helper functions, finds all points with only 1 neighbour in 8 connectivity
    def is_endpoint(skeleton, x, y):
        # Count the number of neighbors (8-connectivity)
        neighbors = np.sum(skeleton[y-1:y+2, x-1:x+2] == 255) - 1 # Subtract 1 to exclude the pixel itself
        return neighbors == 1  # Exactly 1 neighbor indicates an endpoint
    #Helper functions, finds all points with more than 2 neighbours in 8 connectivity
    def is_intersection(skeleton, x, y):
        neighbors = np.sum(skeleton[y-1:y+2, x-1:x+2] == 255)-1
        return neighbors > 2  # More than 2 neighbors means it's an intersection

    #Finds all the endpoints and intersection points in skeletonized picture
    height, width = skeleton.shape
    print(height)
    print(width)
    
    intersection_points = []  
    iterations = 15
    original = skeleton.copy()
    # Thinning step:
    thinned = morphology.thin(skeleton > 0) 
    thinned = (thinned.astype(np.uint8)) * 255

    # Endpoint detection on the thinned skeleton:
    endpoint_coords = []
    intersection_coords = []

    # Extract only foreground pixels for faster iteration
    foreground_pixels = np.argwhere(thinned == 255)  # Returns (y, x) pairs

    #check for endpoints and intersections
    for y, x in foreground_pixels:
        if 1 <= y < height - 1 and 1 <= x < width - 1:  # Ensure we stay within bounds
            if is_endpoint(thinned, x, y):
                endpoint_coords.append((x, y))
            elif is_intersection(thinned, x, y):
                intersection_coords.append((x, y))

    # Create a mask for endpoints and dilate if needed:
    endpoint_mask = np.zeros_like(thinned, dtype=np.uint8)
    for (x, y) in endpoint_coords:
        endpoint_mask[y, x] = 255

    #intersections aren't remoed:
    for (x, y) in intersection_coords:
        endpoint_mask[y, x] = 0  

    
    # Remove endpoints using a dilated mask (if desired):
    kernel = np.ones((3, 3), np.uint8)
    dilated_mask = cv2.bitwise_and(cv2.dilate(endpoint_mask, kernel, iterations=1), original)
    thinned = cv2.subtract(thinned, dilated_mask)
    #cv2.bitwise_not(
    # Update skeleton for the next iteration:
    skeleton = thinned.copy()
         
    endpointstemp = []

    for y in range(0, height):
            for x in range(0, width):
                if skeleton[y,x] == 255 and is_endpoint(skeleton, x, y):
                    endpointstemp.append((x,y))
                if skeleton[y, x] == 255 and is_intersection(skeleton, x, y):
                    intersection_points.append((x, y))
    endpoints = sorted(endpointstemp, key=lambda point: point[0])

    plt.figure(figsize=(10,6))
    plt.title("Pruned image")
    plt.imshow(skeleton, cmap='gray')
    plt.show()
    
    #endpoints = sorted_points
    #Split the sorted array into two arrays
    #mid_index = len(sorted_points) // 2
    #startpoints = sorted_points[:mid_index]  # First half
    #endpoints = sorted_points[mid_index:]  # Second half   
    print(intersection_points)
    
    
    #print(startpoints)
    print(endpoints)
    #print(sorted_points)
    
    #If there´s intersections points, can only handle 1 right now
    if len(intersection_points) > 0:
        skeleton_color = cv2.cvtColor(skeleton, cv2.COLOR_GRAY2BGR)
        for (x, y) in intersection_points:
            cv2.circle(skeleton_color, (x, y), 3, (0, 0, 255), -1)  # Mark intersections in red

        plt.figure(figsize=(10,6))
        plt.imshow(skeleton_color)
        plt.show()
        min_x = (min(point[0] for point in intersection_points) - 1)
        max_x = (max(point[0] for point in intersection_points) + 1)
    else:
        min_x = 0
        max_x = 0
    # Iterate and find all curve elements with specific x value
    def profileline(x):
        
        binary_points = []
        
        # Ensure x is within image bounds
        if 0 <= x < skeleton.shape[1]:
            # Loop over all y-coordinates in the column
            for y in range(skeleton.shape[0]):
                if skeleton[y, x] == 255:  # Binary point (white in binary image)
                    binary_points.append((x, y))  # Append the (x, y) position
       
        result = []
        # Handles if there´s 2 or more neighboring pixels on the profile line, it picks the one with the highest y value
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

    #Helper function that calculates a slope
    def checkslope(point1, point2):
        x = point2[0]-point1[0]
        if x == 0:
            return 0.0
        return (point2[1]-point1[1])/x
    
    #Helper function that interpolates the x value in between 2 points
    def interpolate(x, point1, point2):
        x1 = point1[0]
        y1 = point1[1]
        x2 = point2[0]
        y2 = point2[1]

        if x < x1 or x > x2:
            raise ValueError("x is out of bounds!")
        # Calculate the interpolated y-value
        return y1 + (y2 - y1) * (x - x1) / (x2 - x1)
    
    #Helper functions that rounds .5 and above to 1, and below to 0, to choose the closest matching pixel
    def col_round(x):
        frac = x - math.floor(x)
        if frac < 0.5: return math.floor(x)
        return math.ceil(x)
    # Refined trace function to handle intersections
    def trace_curve_with_gradients(skeleton, start_x, start_y, intersection_start, intesection_end):
        #sets up needed variables
        curve = [(start_x, start_y)]
        visited = set(curve)
        current_x, current_y = start_x, start_y
        localmaximaormin = (start_x,start_y)
        currenttempslope = 999
        counter = 0
        h, w = skeleton.shape
        #Threhsolds used for when wrapping, so it doesn´t interpolate if x is more than 1 pixel away
        height95thresh = (h/100.0)*95.0
        height5thresh = (h/100)*5
        while True:
            neighbors = []
            counter = counter+1
            #(10,10) range(9, 12) (9,9) (9,10) (9,11)
            #Finds all neighbors, except those with -1 x pixel values
            for ny in range(max(0, current_y-1), min(skeleton.shape[0], current_y + 2)):
                for nx in range(max(0, current_x), min(skeleton.shape[1], current_x + 2)):
                    
                    if (nx, ny) != (current_x, current_y) and skeleton[ny, nx] == 255 and (nx, ny) not in visited:
                        neighbors.append((nx, ny))
                #grad = (ny - current_y) / (nx - current_x + 1e-6)
                        
            #Termination needs to be here, but expanded to handle wrapping and non connected curves
            if not neighbors:
                #Termination of while true loop, if last endpoint has no neighbors, or no endpoints is left
                if len(endpoints) == 1 or len(endpoints) == 0:
                    endpoints.pop()
                    break
                
                #Get index number if found endpoint
                tempsave = 0
                temppoint = (current_x, current_y)
                for i in range(len(endpoints)):
                    if temppoint == endpoints[i]:
                        tempsave = i
                #Endpoints are sorted by x, so check all the endspoints with higher x value
                for j in range(tempsave,len(endpoints)):

                    tempendpoint = endpoints[j]
                    #If higher x value
                    if tempendpoint[0] > current_x:
                        #If no wrapping 
                        if not (current_y > height95thresh) and not (tempendpoint[1] < height5thresh):
                            if not (temppoint[1] > height95thresh) and not (current_y < height5thresh):  
                                #Linearly interpolate the space between the 2 found endpoints
                                numofpoints = tempendpoint[0] - current_x
                                for i in range(1,numofpoints):
                                    tempx = current_x+i
                                    ytemp = col_round(interpolate(tempx, temppoint, tempendpoint))
                                    #Avoid ending curve prematurely, by making sure original pixels non interpolated
                                    #Is added to visited
                                    for ny in range(max(0, ytemp-1), min(skeleton.shape[0], ytemp + 2)):
                                        for nx in range(max(0, tempx), min(skeleton.shape[1], tempx + 2)):
                                            if (nx, ny) != (current_x, current_y) and skeleton[ny, nx] == 255 and (nx, ny) not in visited:
                                                visited.add((nx, ny))
                                    visited.add((tempx, ytemp))
                                    curve.append((tempx, ytemp))   
                        #Set current x and y to new endpoint
                        current_x = tempendpoint[0]
                        current_y = tempendpoint[1]
                        #Remove the new endpoint from endpoints list 
                        endpoints.remove(endpoints[j])  
                        #break 
                        break
                #Remove the original endpoint from the endpoint list
                endpoints.remove(endpoints[tempsave])
                #Check for neighbors
                for ny in range(max(0, current_y-1), min(skeleton.shape[0], current_y + 2)):
                    for nx in range(max(0, current_x), min(skeleton.shape[1], current_x + 2)):
                        
                        if (nx, ny) != (current_x, current_y) and skeleton[ny, nx] == 255 and (nx, ny) not in visited:
                            neighbors.append((nx, ny))
                #If no neighbors, terminate
                if len(neighbors) == 0:
                    break
            #Counter used to make sure slope is updated enough
            counter = counter + 1
            #Checks if slope goes from positive to negative or reverse
            #If does, update the new localmaxormin, and reset the counter
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
            
            #Go to next neibor
            current_x, current_y = neighbors[0]  
            #If the next neighbor is in intersection
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
    #Start on first endpoint, and iterate through endpoints
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
        #print(curve)
    return curves
    


xtemp = 0
ytemp = 12000
wtemp = 1250

#testFile = "Profilelinetes/overlaytest0.tif"
#testFile = "C:/Users/willi/OneDrive/Skrivebord/Bachelor/Github/Digitizing-overlapping-curves/Profilelinetest/Simcurve8.tif"
#testFile = "C:/Users/willi/OneDrive/Skrivebord/Bachelor/Github/Digitizing-overlapping-curves/Profilelinetest/muVNT2.tif"
#testFile = "C:/Users/willi/OneDrive/Skrivebord/Bachelor/Github/Digitizing-overlapping-curves/testfolder/fulltext.tif"
#testFile = "C:/Users/willi/OneDrive/Skrivebord/Bachelor/Github/Digitizing-overlapping-curves/wrapping/twowrap2.tif"
#testFile = "C:/Users/willi/OneDrive/Skrivebord/Bachelor/Github/Digitizing-overlapping-curves/Multipleintersections/T00105.las-1v0.tif"
testFile = "C:/Users/willi/OneDrive/Skrivebord/Bachelor/Github/Digitizing-overlapping-curves/Multipleintersections/rotated_image.tif"
#image = cv2.imread(testFile)
#image = cv2.imread(testFile, cv2.IMREAD_GRAYSCALE)
""" cv2.imwrite("testfolder/scantest.png", img) """
img = cv2.imread(testFile, cv2.IMREAD_GRAYSCALE)
image = img[:,2000:3500]
h,w = image.shape
#Choose the region of interest including excat boundries the graph
rx, ry, rw, rh = 0,0, w, h
#rx,ry,rw,rh = cv2.selectROI('Select The Complete and Exact Boundaries of Graph',image)
#graph = image#[ry:ry+rh,rx:rx+rw]
#cv2.destroyWindow('Select The Complete and Exact Boundaries of Graph')

#tempgraph = process_chunks(image.copy())


#Extract the curve points on the image
#image_path = "path_to_your_image.png"
curves = extractCurves(image)

""" curverotated = np.rot90(curves[0])
print(curverotated)
def plot_curve(curve):
    h, w = curve.shape
    x_coords, y_coords = zip(*curve)
    fig, ax = plt.subplots(figsize=(10,5))
    ax.set_xlim(0.0, h)
    ax.set_ylim(0.0, w)
    #plt.figure(figsize=(10, 5))
    ax.plot(x_coords, y_coords, 'b-')
    
    plt.gca().invert_yaxis()  # Match image coordinates
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.show()
    for i, curve in enumerate(curves):
        plot_curve(curve, f"Curve {i + 1}")
        print(curve)
    return curves

plot_curve(curverotated) """
#iio.imwrite("Testresults/plot.tif",curvenum)
#Map curve (x,y) pixel points to actual data points from graph
curve_normalized1 = []
""" for cx, cy in curves[0]:
    x_value = np.float64((cx / rw) * (x_max - x_min) + x_min)
    y_value = np.float64((1 - cy / rh) * (y_max - y_min) + y_min)
    curve_normalized1.append([x_value, y_value]) """
#Lasiotester
import matplotlib.pyplot as plt
import numpy as np

#lasfn = "../T14502Las/T14502_02-Feb-07_JewelryLog.las"
lasfn = "C:/Users/willi/OneDrive/Skrivebord/Bachelor/Github/Digitizing-overlapping-curves/T14502Las/T14502_02-Feb-07_JewelryLog.las"
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
""" for i, k in enumerate(units):
     print(i,k)
     tempdic = las[k]
     x = np.array(tempdic)
     fig, ax = plt.subplots(figsize=(10,20))
     ax.plot(x, depth, color='red', linewidth=1)
     ax.invert_yaxis
     plt.show() """



x = np.array(depth[100:216])
y = np.array(tempGAMM[100:216]) 
wrapcounter = 0
#Enter the min and max values from the source graph here
y_min,y_max = 0.0, 1.0
x_min,x_max = 0.0, 10.0 

#Normalizes the data to chosen x and y bounds
curve_normalized1 = [[np.float64((cx/rw)*(x_max-x_min)+x_min),np.float64((1-cy/rh)*(y_max-y_min)+y_min)] for cx,cy in curves[0]]
curve_normalized1 = np.array(curve_normalized1)

#Handles wrapping
ythreshmin = ((y_max - y_min)/100)*5    
ythreshmax = ((y_max - y_min)/100)*95
maxy = 0
for i in range(len(curve_normalized1)-1):
    curpoint = curve_normalized1[i].copy()
    curpointoriginal = curpoint.copy()
    nextpoint = curve_normalized1[i+1].copy()
    
    if wrapcounter != 0:
        curpoint[1] = (wrapcounter * y_max) + curpoint[1]
        curve_normalized1[i] = curpoint
    if curpoint[1] > maxy:
        maxy = curpoint[1]
    #difference = abs(curpoint[1] - nextpoint[1])
    
    """ if differencepre > ythreshmax:
        wrapcounter += 1 """
    if (curpointoriginal[1] > ythreshmax ) and (nextpoint[1] < ythreshmin):
        wrapcounter += 1

    if (curpointoriginal[1] < ythreshmin ) and (nextpoint[1] > ythreshmax):
        wrapcounter -= 1


temppoint = curve_normalized1[-1].copy()
temppoint[1] = (wrapcounter * y_max) + temppoint[1]
curve_normalized1[-1] = temppoint  
""" if (curpoint[1] < ythreshmax) or (curpoint[1] > ythreshmin):
    continue """   
    

""" for cx, cy in curves[0]:
    normalized_point = [
        np.float64((cx / rw) * (x_max - x_min) + x_min),
        np.float64((1 - cy / rh) * (y_max - y_min) + y_min)
    ]
    curve_normalized1.append(normalized_point)

curve_normalized1 = np.array(curve_normalized1) """
print(curve_normalized1)
np.savetxt("Multipleintersections/2darray.txt", curve_normalized1, fmt='%2f', delimiter=',')

#Plot the simulatedcurve
fig, ax = plt.subplots(figsize=(10,5))
ax.set_xlim(0, 10)
ax.set_ylim(0.0, maxy+ythreshmin)
ax.plot(curve_normalized1[:,0],curve_normalized1[:,1],'o-',linewidth=3)
ax.grid(True)
plt.show()
# Define the function
""" def curve_function1(x):
    return -0.001*x**3 + 0.0042*x**2 + 0.11*x

def curve_function2(x):
    return 0.001*x**3 - 0.0042*x**2 - 0.11*x + 1 """

""" # Generate 500 points for x between 0 and 10
x_values1 = np.linspace(0, 10, 500)
y_values1 = curve_function1(x_values1)

x_values2 = np.linspace(0, 10, 500)
y_values2 = curve_function2(x_values2)

#Same format for print
temparraycurve1 = np.zeros((len(x_values1),2))
for i in range(len(x_values1)):
    temparraycurve1[i] = (x_values1[i], y_values1[i])

testdatacurve1 = np.array(temparraycurve1)
#print(testdatacurve1)

#Same format for print
temparraycurve2 = np.zeros((len(x_values2),2))
for i in range(len(x_values2)):
    temparraycurve2[i] = (x_values2[i], y_values2[i])

testdatacurve2 = np.array(temparraycurve2)
print(testdatacurve2)

from scipy.interpolate import interp1d
from sklearn.metrics import mean_squared_error, mean_absolute_error

#Filter for NAN
testfiltered = testdatacurve2[~np.isnan(testdatacurve2).any(axis=1)]
# Extract x and y from test and real
x_sim, y_sim = curve_normalized1[:, 0], curve_normalized1[:, 1]
x_real, y_real = testfiltered[:, 0], testfiltered[:, 1]

# Interpolate real values
interpolator = interp1d(x_real, y_real, kind='linear', fill_value="extrapolate")
#Interpolate sim
y_real_interp = interpolator(x_sim)

#Mean Square and mean absolute
mse = mean_squared_error(y_sim, y_real_interp)
mae = mean_absolute_error(y_sim, y_real_interp) """

""" print(mse)
print(mae) """