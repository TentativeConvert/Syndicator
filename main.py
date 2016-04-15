#!/usr/bin/python
# -*- coding: utf-8 -*-
########################## IMPORTS AND AUXILIARY CLASSES ###############################
import os, threading, signal, collections, re, more_itertools
import time
import Queue
from gi.repository import Gtk, GObject, GLib
#from gi.repository import AppIndicator3 as AppIndicator
#from gi.repository import Notify

#import classes.DummyProcess as DummyProcess
import ExternalProcess
import Indicator
#import config
import tests.dummyconfig as config

############################### ACTUAL PROGRAM #########################################
# PROGRAM STATES:
# (A) Waiting
#     - at the beginning
#     - each time the user clicks restart
#     No background processes are running in this state.
#     The panel menu has few entries.
# (B) Running
#     The commands selected (backintime, unison ...) are running in the background.
#     The "opening dialog is hidden"
#     The panel menu displays output from backintime/unison ...  and updates icon accordingly
STATE_WAITING = 0
STATE_RUNNING = 1

class UnisonWrapper:
    def __init__(self):
        self.indicator = Indicator.Indicator(function_restart=self.restart,function_quit=self.quit)
        self.process = None
        self.thread = None
        self.lock = threading.Lock()
        self.state = STATE_WAITING
        self.BackUpProcess = ExternalProcess.Process(
            command=config.backup_command,
            output_queue=self.indicator.queue,
            recognized_patterns=config.backup_patterns)            
        #self.BackUpProcess = DummyProcess.Sync(self.indicator.queue)
        self.SyncProcess = ExternalProcess.Process(
            command=config.sync_command,
            output_queue=self.indicator.queue,
            recognized_patterns=config.sync_patterns)
        #self.SyncProcess = DummyProcess.Sync(self.indicator.queue)

    def main(self):
        self.start()
        Gtk.main()

    def quit(self, source):
        self.stop(source) 
        self.indicator.quit()
        Gtk.main_quit()
        print "Syndicator:  Gtk has quit."
                
    def start(self):
        self.lock.acquire()
        self.state = STATE_RUNNING
        self.indicator.set_state(STATE_RUNNING)
        self.lock.release()

        self.thread = threading.Thread(target=self.__run, args=())       
        self.thread.daemon = True
        self.thread.start()

    def restart(self,source):
        self.stop(source)
        self.start()

    def stop(self,source):
        print "Syndicator:  Stopping all ..."
        self.lock.acquire()
        self.state = STATE_WAITING
        self.indicator.set_state(STATE_WAITING)
        self.BackUpProcess.abort()
        self.SyncProcess.abort()
        self.lock.release()
        
        if self.thread:
            if self.thread.isAlive():
                self.thread.join()
                print "Syndicator:  The thread for running subprocesses has joined the main thread."
            self.thread = None 


    def __run(self): # executed in separate thread
        if self.BackUpProcess.run() == 0:
            MIN_WAIT = 2   # two seconds
            MAX_WAIT = 300 # five minutes
            wait_time = MIN_WAIT
            while self.state==STATE_RUNNING: 
                start_time = time.time()
                self.SyncProcess.run()
                elapsed_time = time.time() - start_time
                wait_time = (2-elapsed_time/100)*wait_time
                wait_time = min(max(wait_time,MIN_WAIT),MAX_WAIT)
                self.__count_down(wait_time)

    def __count_down(self,seconds):
        while seconds > 0 and self.state==STATE_RUNNING:
            seconds = seconds - 1
            time.sleep(1)
            self.indicator.queue.put({'type':'status',
                                      'time':'',
                                      'text':'Retrying in %d seconds' %d})
            print "Retrying in %d seconds" % seconds
                

print "Syndicator:  Hello."
GObject.threads_init()
UnisonWrapper().main()
print "Syndicator:  Good bye."

########################################################################################
# Classes:
# (Q) Message queue
# (P) Process class
#    derived program instances:
#       backintime
#       unison
#  each instance has its own recognized messages & failure treatment
#
# (I) Indicator class 
#
# (M) Main class
#     starts the processes
#
# (M) initializes (I) and starts the (P)s
# The (P)s dump things into (Q)
# (I) reads form (Q) and controls (M)
#
#
# Threads:
# (1) GTK-Main:
#     used to be necessary for displaying the opening dialog; 
#     still necessary for reacting to mouse clicks on the indicator!
# (2) Thread for running the subprocesses:  
#     This is a single thread started automatically in UnisonWrapper().main()
#     executing the function UnisonWrapper.__run().
#     The thread can be interupted and restarted via a menu entry of the indicator.
#
#     Messages should be evaluated and fed into message queue in standardized format:
#       (menu message, [dialoge message])
#     [There's no longer any need for a separate "terminate" action:
#       The "opening dialogue" has gone.
#       The menu item may always read "Restart" instead of "Start".
#       There's no "waiting state" – only "failure state".]
#
# (3) A thread for reading from message queue (at intervals):
#       This thread runs constantly in the background;
#       it updates the indicator according to whatever it finds in the message queue
