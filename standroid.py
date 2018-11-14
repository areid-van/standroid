from bottle import route, run, abort, static_file
import RPi.GPIO as GPIO
import thread
import threading
import time
import os

global docroot
docroot = os.path.dirname(os.path.abspath(__file__)) + '/assets'

def moveUp(t):
    GPIO.setup(3, GPIO.IN)
    GPIO.setup(5, GPIO.OUT)
    GPIO.output(5, 0)
    time.sleep(t)
    GPIO.setup(5, GPIO.IN)
    global motionLock
    motionLock.release()

def moveDown(t):
    GPIO.setup(3, GPIO.OUT)
    GPIO.output(3, 0)
    GPIO.setup(5, GPIO.OUT)
    GPIO.output(5, 0)
    time.sleep(t)
    GPIO.setup(5, GPIO.IN)
    GPIO.setup(3, GPIO.IN)
    global motionLock
    motionLock.release()
    

GPIO_TRIGGER = 16
GPIO_ECHO = 18

def readDistance():
    GPIO.output(GPIO_TRIGGER, True)
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)

    StartTime = time.time()
    StopTime = time.time()
    BeginTime = time.time()

    while GPIO.input(GPIO_ECHO) == 0:
        StartTime = time.time()
        if StartTime - BeginTime > 0.1: raise IOError

    while GPIO.input(GPIO_ECHO) == 1:
        StopTime = time.time()
        if StopTime - BeginTime > 0.1: raise IOError

    TimeElapsed = StopTime - StartTime
    distance = (TimeElapsed * 34300) / 2

    return distance

def distance():
    count = 0
    d = 0
    for i in range(4):
        try:
            d += readDistance()
            count += 1
        except IOError:
            pass

    if count < 2: raise IOError("Device error")
    return d/count

@route('/height')
def height():
    return '%f' % distance()

@route('/height/<h>')
def setheight(h):
    try:
        h = float(h)
    except ValueError:
        abort(400)

    d = distance()

    if h > d:
        t = (h - d)/8
        return "moving up %f" % t
    else:
        t = (d - h)/8
        return "moving down %f" % t

@route('/up/<t>')
def up(t):
    try:
        t = float(t)
    except ValueError:
        abort(400)

    global motionLock
    if not motionLock.acquire(False): abort(409)
    thread.start_new_thread(moveUp, (t,))

@route('/down/<t>')
def down(t):
    try:
        t = float(t)
    except ValueError:
        abort(400)

    global motionLock
    if not motionLock.acquire(False): abort(409)
    thread.start_new_thread(moveDown, (t,))

@route('/')
def server_static():
    global docroot
    return static_file('standroid.html', root=docroot)

@route('/static/<filename:path>')
def send_static(filename):
    global docroot
    return static_file(filename, root=docroot)


GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)

global motionLock
motionLock = threading.Lock();
run(host='0.0.0.0', port=80, debug=True)
