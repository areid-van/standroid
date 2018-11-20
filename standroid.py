from bottle import route, run, abort, static_file
import RPi.GPIO as GPIO
import thread
import threading
import time
import os
import json

global docroot
docroot = os.path.dirname(os.path.abspath(__file__)) + '/assets'

def moveUp(t):
    print("Move up %f"%t)
    GPIO.setup(3, GPIO.IN)
    GPIO.setup(5, GPIO.OUT)
    GPIO.output(5, 0)
    time.sleep(t)
    GPIO.setup(5, GPIO.IN)

def moveDown(t):
    print("Move down %f"%t)
    GPIO.setup(3, GPIO.OUT)
    GPIO.output(3, 0)
    GPIO.setup(5, GPIO.OUT)
    GPIO.output(5, 0)
    time.sleep(t)
    GPIO.setup(5, GPIO.IN)
    GPIO.setup(3, GPIO.IN)
    

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
        if StartTime - BeginTime > 0.2: raise IOError

    while GPIO.input(GPIO_ECHO) == 1:
        StopTime = time.time()
        if StopTime - BeginTime > 0.2: raise IOError

    TimeElapsed = StopTime - StartTime
    distance = (TimeElapsed * 34300) / 2

    return distance

def distance(samples=100, delay=0.01, retry=10):
    ecount = 0
    d = list()
    for i in range(samples+retry):
        if len(d) == samples: break
        time.sleep(delay)
        try:
            d.append(readDistance())
        except IOError:
            if ecount < retry:
                ecount += 1
                pass
            else:
                raise

    d = [x for x in d if 25 < x < 175]
    x1 = len(d)//4
    x2 = x1+len(d)//2
    d = sorted(d)[x1:x2]
    return sum(d)/len(d)


SPEED_UP = 4
SPEED_DOWN = 4

def moveTo(h):
    print("move to %f"%h)
    for i in range(2):
        d = distance()
        print("height %f"%d)

        if h > d:
            t = (h - d)/SPEED_UP
            moveUp(t)
        else:
            t = (d - h)/SPEED_DOWN
            moveDown(t)
    print("final height %f"%distance())

def doCalibrate(t):
    moveDown(t+2)
    h1 = distance()
    print("h1 %f"%h1)
    moveUp(t)
    h2 = distance()
    print("h2 %f"%h2)
    global SPEED_UP
    SPEED_UP = (h2 - h1)/t
    moveUp(2)
    h2 = distance()
    print("h2 %f"%h2)
    moveDown(t)
    h1 = distance()
    print("h1 %f"%h1)
    global SPEED_DOWN
    SPEED_DOWN = (h2 - h1)/t
    with open('standroid.json', 'w') as outfile:
        json.dump([SPEED_UP, SPEED_DOWN], outfile)

def opAndRelease(op, arg):
    op(arg)
    global motionLock
    motionLock.release()
 
@route('/speed')
def speed():
    return '{up: %f, down: %f}' % (SPEED_UP, SPEED_DOWN)

@route('/calibrate')
def calibrate():
    global motionLock
    if not motionLock.acquire(False): abort(409)
    thread.start_new_thread(opAndRelease, (doCalibrate, 5))

@route('/height')
def height():
    return '%f' % distance()

@route('/height/<h>')
def height2(h):
    try:
        h = float(h)
    except ValueError:
        abort(400)

    global motionLock
    if not motionLock.acquire(False): abort(409)
    thread.start_new_thread(opAndRelease, (moveTo, h))

@route('/up/<t>')
def up(t):
    try:
        t = float(t)
    except ValueError:
        abort(400)

    global motionLock
    if not motionLock.acquire(False): abort(409)
    thread.start_new_thread(opAndRelease, (moveUp, t))

@route('/down/<t>')
def down(t):
    try:
        t = float(t)
    except ValueError:
        abort(400)

    global motionLock
    if not motionLock.acquire(False): abort(409)
    thread.start_new_thread(opAndRelease, (moveDown, t))

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

try:
    with open('standroid.json', 'r') as infile:
        config = json.load(infile)
        SPEED_UP = config[0]
        SPEED_DOWN = config[1]
except:
    pass

global motionLock
motionLock = threading.Lock();
run(host='0.0.0.0', port=80, debug=True)
