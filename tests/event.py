#!/usr/bin/python
# -*- coding: utf-8 -*-

import threading, time

print "Creating event ..."
e = threading.Event()
l = threading.Lock()

def A():
    while True:
        l.acquire()
        print "    Lock acquired."
        print "    Sleeping ..."
        time.sleep(2)
        print "    Waking up ... raising event."
        e.set()
        print "    Quitting."
        l.release()
        print "    Lock released."
        time.sleep(0.00001)

print "Creating thread ..."
threadA = threading.Thread(target=A)
print "Starting thread ..."
threadA.start()

while True:
    print "Waiting for event ..."
    e.wait()
    print "Event has occured."
    l.acquire()
    print "Lock acquired."
    print "Sleeping ..."
    time.sleep(3)
    l.release()
    print "Lock released."
    e.clear()
    print "Event cleared."

    
