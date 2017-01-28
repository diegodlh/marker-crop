import cv2
import cv2.aruco as aruco
import sys, math

MARKER_EVEN_SIDE = 0
MARKER_EVEN_TOP = 1
MARKER_ODD_SIDE = 2
MARKER_ODD_TOP = 3

markerDictionary = aruco.Dictionary_create(4, 5)

borderWidth = 15

# Transpose and flip the image as specified. Also transpose and flip
# the corner coordinates in the same way so we don't have to
# recalculate them.
def transposeFlipCorners(shouldTranspose, flipType, image, corners):
  if shouldTranspose:
    image = cv2.transpose(image)
    for box in corners:
      for point in box[0]:
        temp = point[0]
        point[0] = point[1]
        point[1] = temp
  rows, cols, z = image.shape
  for box in corners:
    for point in box[0]:
      if flipType == 0 or flipType < 0:
        point[1] = rows - point[1]
      if flipType == 1 or flipType < 0:
        point[0] = cols - point[0]
  cv2.flip(image, flipType, image)
  return image

# Rotate both the image and the corners so that the example is facing
# the right direction. Only rotate 0, 90, 180, or 270 degrees.
def rotateImage(example, image, corners):
  angleRad = math.atan2(example[3][1] - example[0][1],
                        example[3][0] - example[0][0]) - math.pi/2
  angle = angleRad * 180 / math.pi
  if angle > 70 and angle < 110:
    image = transposeFlipCorners(True, 0, image, corners)
  elif angle > 160 and angle < 200:
    image = transposeFlipCorners(False, -1, image, corners)
  elif (angle > 250 and angle < 290) or (angle > -110 and angle < -70):
    image = transposeFlipCorners(True, 1, image, corners)
  return image

# Completely process an image, rotating it so the tokens face upwards
# and cropping to the markers
def process(image):
  gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
  parameters = aruco.DetectorParameters_create()

  corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, markerDictionary,
                                                        parameters=parameters)

  isOdd = calculateOdd(ids)
  sides = findSides(corners, ids, isOdd)
  topBottom = findTopBottom(corners, ids, isOdd)
  if len(sides) != 2 or len(topBottom) != 2:
    sys.stderr.write("Error finding markers!\n")
    exit(1)
  image = rotateImage(sides[0], image, corners)

  leftBorder, rightBorder = processSides(sides, isOdd)
  topBorder, bottomBorder = processTopBottom(topBottom)
  return image[topBorder:bottomBorder, leftBorder:rightBorder]

# Figure out if we are processing an odd page (True) or an even page (False)
def calculateOdd(ids):
  oddCount = 0
  evenCount = 0
  for item in ids:
    if item == MARKER_EVEN_SIDE or item == MARKER_EVEN_TOP:
      evenCount += 1
    if item == MARKER_ODD_SIDE or item == MARKER_ODD_TOP:
      oddCount += 1
  return oddCount >= evenCount

# Search through the ids and return the side corner lists
def findSides(corners, ids, isOdd):
  result = []
  for i in xrange(0, len(ids)):
    if ((isOdd and ids[i] == MARKER_ODD_SIDE) or
        (not isOdd and ids[i] == MARKER_EVEN_SIDE)):
      result.append(corners[i][0])
  return result

# Search through the ids and return the top and bottom corner lists
def findTopBottom(corners, ids, isOdd):
  result = []
  for i in xrange(0, len(ids)):
    if ((isOdd and ids[i] == MARKER_ODD_TOP) or
        (not isOdd and ids[i] == MARKER_EVEN_TOP)):
      result.append(corners[i][0])
  return result

# Take the two side tokens and figure out which is left and
# right. Return the X coordinates of the resulting crop.
def processSides(sides, isOdd):
  left = sides[0]
  right = sides[1]
  if left[0][0] > right[0][0]:
    temp = left
    left = right
    right = temp
  if isOdd:
    leftBorder = max(left[0][0], left[3][0]) + borderWidth
    rightBorder = min(right[0][0], right[3][0]) - borderWidth
  else:
    leftBorder = max(left[1][0], left[2][0]) + borderWidth
    rightBorder = min(right[1][0], right[2][0]) - borderWidth
  return int(leftBorder), int(rightBorder)

# Take the two top/bottom tokens and figure out which is the top and
# which is the bottom. Return the Y coordinates of the resulting crop
def processTopBottom(topBottom):
  top = topBottom[0]
  bottom = topBottom[1]
  if top[0][1] > bottom[0][1]:
    temp = top
    top = bottom
    bottom = temp
  topBorder = max(top[2][1], top[3][1]) + borderWidth
  bottomBorder = min(bottom[0][1], bottom[1][1]) - borderWidth
  return int(topBorder), int(bottomBorder)

def main():
  if len(sys.argv) != 3:
    sys.stderr.write("Usage: crop <infile> <outfile>\n")
    exit(1)
  else:
    inFile = sys.argv[1]
    outFile = sys.argv[2]
    image = cv2.imread(inFile)
    result = process(image)
    cv2.imwrite(outFile, result)

main()