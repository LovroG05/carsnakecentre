import cv2

img = cv2.imread('frames/1650969997.2056324.jpg')

ROI = cv2.selectROI("", img)

print(ROI)