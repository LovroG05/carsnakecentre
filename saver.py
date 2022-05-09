import threading, time, cv2, sys
from csv import writer


class SaveThread(threading.Thread):
    def __init__(self, threadID, frame, steering_value, gas_value, path):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = "SaveThread"
        self.frame = frame
        self.steering_value = steering_value
        self.path = path
        
    def run(self):
        print("Starting " + self.name + ": " + str(self.threadID))
        #h,  w = self.frame.shape[:2]
        #newcameramtx, roi=cv2.getOptimalNewCameraMatrix(MAT, DIST, (w, h), 1, (w, h))
        #dst = cv2.undistort(self.frame, MAT, DIST, None, newcameramtx)
        t = time.time()
        cv2.imwrite(self.path + str(t) + ".jpg", self.frame)
        with open("framedata.csv", "a") as file:
            writer_ = writer(file, delimiter=',', quotechar='"')
            writer_.writerow([self.path + str(t) + ".jpg", str(self.steering_value), str(self.gas_value)])
            file.close()
            
        print("Exiting " + self.name + ": " + str(self.threadID))
        sys.exit()