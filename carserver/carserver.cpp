#include <opencv2/opencv.hpp>
#include "sys/types.h"
#include "sys/sysinfo.h"
#include <nadjieb/mjpeg_streamer.hpp>

using namespace nadjieb;
using namespace cv;
using namespace std;

// for convenience
using MJPEGStreamer = MJPEGStreamer;

int main() {
    VideoCapture cap(0);
    if (!cap.isOpened()) {
        cerr << "VideoCapture not opened\n";
        exit(EXIT_FAILURE);
    }

    vector<int> params = {IMWRITE_JPEG_QUALITY, 90};

    MJPEGStreamer streamer;

    // By default "/shutdown" is the target to graceful shutdown the streamer
    // if you want to change the target to graceful shutdown:
    //      streamer.setShutdownTarget("/stop");

    // By default 1 worker is used for streaming
    // if you want to use 4 workers:
    //      streamer.start(8080, 4);
    streamer.start(6969, 2);

    // Visit /shutdown or another defined target to stop the loop and graceful shutdown
    while (streamer.isRunning()) {
        Mat frame;
        cap >> frame;
        if (frame.empty()) {
            cerr << "frame not grabbed\n";
            exit(EXIT_FAILURE);
        }

        resize(frame, frame, Size(640, 480));

        // http://localhost:6969/bgr
        vector<uchar> buff_bgr;
        imencode(".jpg", frame, buff_bgr, params);
        streamer.publish("/bgr", string(buff_bgr.begin(), buff_bgr.end()));

        this_thread::sleep_for(chrono::milliseconds(10));
    }

    streamer.stop();
}


