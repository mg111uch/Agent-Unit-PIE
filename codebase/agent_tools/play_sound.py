from playsound import playsound
import time
import datetime

while True:
    min = datetime.datetime.now().minute # the current minute
    sec = datetime.datetime.now().second #the current second
    if sec == 0: # and min%3 == 0:
        playsound('censor-beep-1sec-8112.mp3')
    # if sec == 0 and min%3 == 0:
    #     playsound('086300_beep-tone-47912.mp3')
    
    time.sleep(1)
