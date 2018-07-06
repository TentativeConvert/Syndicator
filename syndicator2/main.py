#!/usr/bin/python
# -*- coding: utf-8 -*-
########################## IMPORTS AND AUXILIARY CLASSES ###############################
import os, threading
#import signal, collections, re, more_itertools, GLib
import time
from gi.repository import Gtk, GObject

#import classes.DummyProcess as DummyProcess
from ExternalProcess import ExternalProcess
from Indicator import Indicator
import config
#import tests.dummyconfig as config

############################### ACTUAL PROGRAM #########################################
class Syndicator:
    STATE_PAUSED = 0
    STATE_RUNNING = 1
    
    def __init__(self):
        self.indicator = Indicator(function_restart=self.restart,
                                   function_pause=self.stop,
                                   function_quit=self.quit,
                                   icon_default=config.icon_default,
                                   icon_paused=config.icon_paused)
        self.process = None
        self.thread = None
        self.state_lock = threading.Lock()
        self.state = Syndicator.STATE_PAUSED
        self.BackUpProcess = ExternalProcess(
            command=config.backup_command,
            recognized_patterns=config.backup_patterns,
            icon_working=config.backup_icon_working,
            report_status = self.indicator.new_status,
            report_error= self.indicator.new_error,
            report_file = self.indicator.new_file,
            report_notification = self.indicator.new_notification
        )            
        self.SyncProcess = ExternalProcess(
            command=config.sync_command,
            recognized_patterns=config.sync_patterns,
            icon_working=config.sync_icon_working,
            report_status = self.indicator.new_status,
            report_error= self.indicator.new_error,
            report_file = self.indicator.new_file,
            report_notification = self.indicator.new_notification
        )
        #self.BackUpProcess = DummyProcess.Sync(self.indicator.queue)
        #self.SyncProcess = DummyProcess.Sync(self.indicator.queue)

    def main(self):
        self.start()
        Gtk.main()

    def quit(self, source):
        #There's currently no way to invoke this function!
        self.stop(source) 
        self.indicator.quit()
        Gtk.main_quit()
        print "Syndicator:  Gtk has quit."
                
    def start(self):
        self.state_lock.acquire()
        self.state = Syndicator.STATE_RUNNING
        self.state_lock.release()
        self.indicator.start()
        self.thread = threading.Thread(target=self.__run, args=())       
        self.thread.daemon = True
        self.thread.start()

    def restart(self,source):
        self.stop(source)
        self.start()

    def stop(self,source):
        print "Syndicator:  Stopping all ..."
        self.state_lock.acquire()
        self.state = Syndicator.STATE_PAUSED
        self.indicator.pause()
        self.BackUpProcess.abort()
        self.SyncProcess.abort()
        self.state_lock.release()
        
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
            while self.state==Syndicator.STATE_RUNNING: 
                start_time = time.time()
                self.SyncProcess.run()
                elapsed_time = time.time() - start_time
                wait_time = (2-elapsed_time/100)*wait_time
                wait_time = min(max(wait_time,MIN_WAIT),MAX_WAIT)
                self.__count_down(wait_time)

    def __count_down(self,seconds):
        while seconds > 0 and self.state==Syndicator.STATE_RUNNING:
            seconds = seconds - 1
            time.sleep(1)
            self.indicator.new_status("Restarting in %d seconds ..." %seconds)

print "Syndicator:  Hello."
GObject.threads_init()
Syndicator().main()
print "Syndicator:  Good bye."

########################################################################################
# Classes:
# (P) ExternalProcess
#    derived program instances:
#       backintime
#       unison
#  each instance has its own recognized messages & failure treatment
#
# (I) Indicator
#
# (M) Main class
#     starts the processes
#
# (M) initializes (I) and starts the (P)s.
# It passes the 'input functions of I' (new_status, new_error, ...)
# to the constructors of (P).
#
#
# Threads:
# (1) The main thread:
#     Executes Gtk.main() so that the indicator menu can react to mouse input.
# (2) A thread in (M) for running the subprocesses:
#     This is a single thread started automatically in Syndicator().main()
#     executing the function Syndicator.__run().
#     The thread can be interrupted and restarted via a menu entry of the indicator.
# (3) A thread in (I) periodically updating the icon and the menu entries:
#     This thread runs in an infinite loop, waiting on each turn for an 'update_event'.
       
