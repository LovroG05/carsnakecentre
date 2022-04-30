import cv2
import numpy as np


cam = cv2.VideoCapture("http://192.168.138.57:8000/")



while True:
    ret, frame = cam.read()
    a = np.array([(0,280), (int(cam.get(3)),280), (0,200), (int(cam.get(3)),200)])
    cv2.drawContours(frame, [a], 0, (0,255,0), 2)
    cv2.imshow("test", frame)
    cv2.waitKey(1)