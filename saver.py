import threading, time, cv2, sys
from csv import writer


class SaveThread(threading.Thread):
    def __init__(self, threadID, frame):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = "SaveThread"
        self.frame = frame
        
    def run(self):
        print("Starting " + self.name + ": " + str(self.threadID))
        #h,  w = self.frame.shape[:2]
        #newcameramtx, roi=cv2.getOptimalNewCameraMatrix(MAT, DIST, (w, h), 1, (w, h))
        #dst = cv2.undistort(self.frame, MAT, DIST, None, newcameramtx)
        global STEERING_VALUE, GAS_VALUE, BRAKE_VALUE, DIRECTION, FRAMEPATH
        t = time.time()
        cv2.imwrite(FRAMEPATH + str(t) + ".jpg", self.frame)
        with open("framedata.csv", "a") as file:
            writer_ = writer(file, delimiter=',', quotechar='"')
            writer_.writerow([FRAMEPATH + str(t) + ".jpg", str(STEERING_VALUE), str(GAS_VALUE), str(BRAKE_VALUE), str(DIRECTION)])
            file.close()
            
        print("Exiting " + self.name + ": " + str(self.threadID))
        sys.exit()