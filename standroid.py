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
global motionLock
motionLock = threading.Lock();
run(host='0.0.0.0', port=80, debug=True)
