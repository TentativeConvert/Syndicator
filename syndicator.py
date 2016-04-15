#!/usr/bin/python
import os, threading, signal
from subprocess import Popen, PIPE, STDOUT
from gi.repository import Gtk
from gi.repository import AppIndicator3 as AppIndicator

class my_indicator:
    ICON_0 = "gtk-home" 
    ICON_1 = "gtk-help"       

    def __init__(self, wrapper):
        self.ind = AppIndicator.Indicator.new("my-app-indicator", Gtk.STOCK_INFO, AppIndicator.IndicatorCategory.SYSTEM_SERVICES)
        self.ind.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self.wrapper = wrapper
        self.build_menu()

    def build_menu(self):
        item_quit = Gtk.MenuItem('Quit')
        item_quit.connect('activate', self.wrapper.quit)
        menu = Gtk.Menu()
        self.ind.set_menu(menu)
        menu.append(item_quit)
        menu.show_all()

    def update_icon(self,icon):
        self.ind.set_icon(icon)

class dummy_wrapper:
    PROGRAM = "./dummyprogram.sh"

    def __init__(self):
        self.indicator = my_indicator(self)

    def main(self):
        self.process = Popen(self.PROGRAM, stdout=PIPE, stderr=STDOUT, close_fds=True, shell=True, preexec_fn=os.setsid)
        self.thread = threading.Thread(target=self.watch_pipe, args=(self.process.stdout,self.indicator))
        self.thread.daemon = True
        self.thread.start() 
        Gtk.main()

    def quit(self, source):
        if self.process:
            print "Terminating process ..."
            os.killpg(self.process.pid, signal.SIGTERM)               
        if self.thread:
            print "Waiting for thread to end ..."
            self.thread.join() 
        print "Quitting Gtk ..." 
        Gtk.main_quit()

    @staticmethod
    def watch_pipe(pipe, indicator): 
        while 1:  
            line = pipe.readline().strip() 
            # The thread waits here until a line appears in the pipe.
            if not line: 
                # This happens exactly once, namely when the process ends.
                break
            else:
                print line
                if line=="0": 
                    indicator.update_icon(my_indicator.ICON_0)
                else:
                    indicator.update_icon(my_indicator.ICON_1)  
        print "Closing pipe-watcher."

dummy_wrapper().main()
