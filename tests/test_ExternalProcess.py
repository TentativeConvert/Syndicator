#!/usr/bin/python
########################## IMPORTS AND AUXILIARY CLASSES ###############################
import time, threading, Queue

import dummyconfig as config

import ExternalProcess as ExternalProcess

message_queue = Queue.Queue()
Unison = ExternalProcess.Process(command = config.sync_command,output_queue=message_queue,recognized_patterns=config.sync_patterns)

def runprogramme():
    exit_status = Unison.run()
    print "exit status = " + str(exit_status)

print "starting thread ..."
thread = threading.Thread(target=runprogramme,)
thread.daemon = True
thread.start() 

time.sleep(3)

Unison.abort()
#if thread:
#    if thread.isAlive():
thread.join()
print "Subthread has joined main thread."
print "Contents of queue: "
try:
    while True:
        print message_queue.get(block=False) 
        message_queue.task_done()                  
except Queue.Empty:
    print "END"
        

