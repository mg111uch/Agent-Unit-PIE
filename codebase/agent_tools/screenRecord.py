import numpy as np
# import cv2 as cv
# import sys,datetime,time

'''
import easyocr
reader = easyocr.Reader(['en'], gpu=False)
result = reader.readtext("nifty1.png", detail = 0)
print(result)
# for (bbox, text, prob) in result:
#   print(f'Text: {text}, Probability: {prob}')
'''

'''
import mss, mss.tools
# import pytesseract

# cv.namedWindow("Live", cv.WINDOW_NORMAL)
# cv.resizeWindow("Live", 800, 640)

with mss.mss() as sct:
    monitor = {"top": 0, "left": 0, "width": 800, "height": 640}
    while True:
        # sct_img = sct.grab(monitor)
        # img = np.array(sct_img)
        img = cv.imread("nifty1.png")
        frame = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

        # text = pytesseract.image_to_string(frame)
        # print(text)
        
        cv.imshow('Live', frame)
        if cv.waitKey(1) == ord('q'):
            break
    # mss.tools.to_png(sct_img.rgb, sct_img.size, output=filename)
cv.destroyAllWindows()
'''
###############################
###  For Images to Video    ###
###############################
import cv2
import os

print(cv2.__version__)

image_folder = 'img2vid'
video_name = 'video.avi'

# images = [img for img in os.listdir(image_folder) if img.endswith(".png")]
# frame = cv2.imread(os.path.join(image_folder, images[0]))
# height, width, layers = frame.shape

# video = cv2.VideoWriter(video_name, 0, 1, (width,height))
img = cv2.imread("nifty1.png")
cv2.imshow('GUI Name', img)
# for image in images:
#     video.write(cv2.imread(os.path.join(image_folder, image)))

# cv2.destroyAllWindows()
# video.release()
###############################
###  For WebCam Recording   ###
###############################
''' 
# resolution = (640, 480)
# codec = cv.VideoWriter_fourcc(*"XVID")
# filename = "Recording.avi"
# fps = 20.0
# out = cv.VideoWriter(filename, codec, fps, resolution)

import mediapipe as mp

mp_holistic = mp.solutions.holistic
holistic_model = mp_holistic.Holistic(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
 
# Initializing the drawing utils for drawing the facial landmarks on image
mp_drawing = mp.solutions.drawing_utils

capture = cv.VideoCapture(0) 

previousTime = 0
currentTime = 0

while capture.isOpened():
    ret, frame = capture.read()
    # out.write(frame)    # For Saving Video Frames

    frame = cv.resize(frame, (800, 600))
    image = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
 
    image.flags.writeable = False
    results = holistic_model.process(image)
    image.flags.writeable = True
 
    # Converting back the RGB image to BGR
    image = cv.cvtColor(image, cv.COLOR_RGB2BGR)
 
    # Drawing the Facial Landmarks
    mp_drawing.draw_landmarks(
      image,
      results.face_landmarks,
      mp_holistic.FACEMESH_CONTOURS,
      mp_drawing.DrawingSpec(
        color=(255,0,255),
        thickness=1,
        circle_radius=1
      ),
      mp_drawing.DrawingSpec(
        color=(0,255,255),
        thickness=1,
        circle_radius=1
      )
    )
 
    # Drawing Right hand Land Marks
    mp_drawing.draw_landmarks(
      image, 
      results.right_hand_landmarks, 
      mp_holistic.HAND_CONNECTIONS
    )
 
    # Drawing Left hand Land Marks
    mp_drawing.draw_landmarks(
      image, 
      results.left_hand_landmarks, 
      mp_holistic.HAND_CONNECTIONS
    )
     
    currentTime = time.time()
    fps = 1 / (currentTime-previousTime)
    previousTime = currentTime
     
    cv.putText(image, str(int(fps))+" FPS", (10, 70), cv.FONT_HERSHEY_COMPLEX, 1, (0,255,0), 2)
    cv.imshow('frame', image)
    if cv.waitKey(1) == ord('q'):
        break

capture.release()
# out.release()
cv.destroyAllWindows()
'''
