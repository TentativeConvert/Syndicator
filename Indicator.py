#!/usr/bin/python
# -*- coding: utf-8 -*-
########################## IMPORTS AND AUXILIARY CLASSES ###############################
import threading, collections 
import time
import Queue
from gi.repository import Gtk, GObject, GLib
from gi.repository import AppIndicator3 as AppIndicator
from gi.repository import Notify

ICONS_WORKING = ["network-transmit","network-receive"]#ubuntu-client-updating
ICON_WAITING =  "network-idle"    #ubuntuone-client-paused"

STATE_WAITING = 0
STATE_RUNNING = 1

class Indicator:
    """Panel icon and menu"""
    def __init__(self, function_restart, function_quit): 
        self.appindicator = AppIndicator.Indicator.new("unison-indicator", Gtk.STOCK_INFO, AppIndicator.IndicatorCategory.SYSTEM_SERVICES)
        self.appindicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        Notify.init("unison-indicator")
        self.notification = Notify.Notification.new("<b>Unison</b>","",None) # balloon notification
        # internal data:
        self.status_list = collections.deque(maxlen=20)
        self.error_list = collections.deque(maxlen=10)
        self.log_list = collections.deque(maxlen=30)
        self.icon = ""
        self.notifytext = ""
        self.notifyheading = ""
        self.notifyicon = ""
        # queue for receiving updates:
        self.queue = Queue.Queue()  
        # entries should have the format [type, time, header, text, icon]
        # where type is one of {status, log, error, notification}
        # e.g. 
        #    message = {'type':"notification",
        #               'time':"12:43",
        #               'heading':"Unison",
        #               'text':"Sync complete","
        #               'icon':"OK"}
        # Values are retrieved via
        #    message['icon']
        # etc. 
        self.icons_working = ICONS_WORKING
        self.icon_waiting = ICON_WAITING

        def build_menu(function_restart,function_quit):
            self.menu = Gtk.Menu()
            self.menu_log_list = Gtk.Menu()
            self.menu_error_list = Gtk.Menu()
            self.item_start   = Gtk.MenuItem('Start ...')
            self.item_quit    = Gtk.MenuItem('Quit')
            self.item_log_list = Gtk.MenuItem('Recently changed files')
            self.item_error_list = Gtk.MenuItem('Error log')
            self.menu_log_list.append(Gtk.MenuItem('--'))
            self.menu_error_list.append(Gtk.MenuItem('--'))
            self.item_status = Gtk.MenuItem('')
            self.item_status.connect('activate',self.show_status_in_dialog)
            self.item_start.connect('activate', function_restart)
            self.item_quit.connect('activate', function_quit)
            self.item_log_list.set_submenu(self.menu_log_list)
            self.item_error_list.set_submenu(self.menu_error_list)
            menu_items = [self.item_status,
                          self.item_log_list,
                          self.item_error_list,
                          Gtk.SeparatorMenuItem(),
                          self.item_start,
                          self.item_quit]
            for item in menu_items:
                self.menu.append(item)
            self.appindicator.set_menu(self.menu)
            self.status_list.appendleft({'time':time.strftime("%H:%M"),'text':"Initializing ..."})
            self.menu.show_all()
        build_menu(function_restart,function_quit)
        self.set_state(STATE_WAITING) 
        self.watch_thread = threading.Thread(target=self.__watch_queue)
        self.watch_thread.daemon = True
        self.watch_thread.start()
                
    def quit(self):
        print "Indicator:  Quitting."
        Notify.uninit()

    def set_state(self,state):
        """Sets state to 'Waiting' or 'Running' and updates menu accordingly."""
        self.state = state
        if state==STATE_RUNNING:
            self.item_start.get_child().set_text("Restart ...")
        else:
            self.item_start.get_child().set_text("Start ...")
            self.appindicator.set_icon(self.icon_waiting)
           
    def show_status_in_dialog(self,source):
        """Shows a message dialog displaying the full current status message;
           called when user clicks on the (shortened) status message in the panel menu"""        
        dialog = Gtk.MessageDialog(type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK, message_format="Back-in-time/unison report:")
        display_list = ["[%s] %s" % (entry['time'],entry['text']) for entry in reversed(self.status_list)]
        dialog.format_secondary_text("\n".join(display_list) + "\n\nFor further details, please consult the log-file.")
        dialog.run()
        dialog.destroy()
    
#    def new_status(self,text,icon):
#        self.status_list.appendleft({'time':msg['time'],'text':msg['text']})
#        self.icon = msg['icon']
    
    def add_message_to_queue(self,message):
        self.message_queue.put(message)   
        
    def __watch_queue(self):
        """
        main process of this class;
        runs indefinitly in the separate thread watch_thread
        """
        def process_message(msg):
            print "Indicator:  Processing message of type [%s]" % msg['type']
            if msg['type'] == 'status':
                self.status_list.appendleft({'time':msg['time'],'text':msg['text']})
                self.icon = msg['icon']
            elif msg['type'] == 'log':
                # Remove older entries concerning the same file,
                # so that each file is listed at most once:
                for entry in list(self.log_list):
                    # list(...) is needed because log_list is mutated within the for loop
                    if entry['text'] == msg['text']:
                        self.log_list.remove(entry)
                self.log_list.appendleft({'time':msg['time'],'text':msg['text']})
            elif msg['type'] == 'error':
                self.error_list.appendleft({'time':msg['time'],'text':msg['text']})
            elif msg['type'] == 'notification':
                self.notifyheading = msg['heading']
                self.notifytext = msg['text']
                self.notifyicon = msg['icon']
        def process_queue(q):
            """
            If queue is empty, wait.
            If not, run through the whole queue and process each item.
            """
            msg = q.get(block=True)
            process_message(msg)
            q.task_done()
            try:
                while True:
                    msg = q.get(block=False) 
                    process_message(msg)
                    q.task_done()                  
            except Queue.Empty:
                return
            return  #this line should never be reached, but the interpreter wants it here

        while True:
            process_queue(self.queue)
            GLib.idle_add(self.__update_appearances)
            time.sleep(0.2)

    def __update_appearances(self):
        #update notification:
        if self.notifyheading != "":
            self.notification.update("<b>" + self.notifyheading + "</b>",self.notifytext,self.notifyicon)
            self.notification.show()
            self.notifyheading = ""
        #update icon:
        if self.icon=="":
            try: 
                self.blink_counter = (self.blink_counter + 1) % len(self.icons_working)
            except AttributeError: self.blink_counter = 0 
            self.icon = self.icons_working[self.blink_counter]
        self.appindicator.set_icon(self.icon)
        #update status text:
        if self.status_list[0]:
            msg = self.status_list[0]
            text = msg['text']
            if len(text) > 50:
                text = text[:24] + "..." + text[-24:]
            text = "[" + msg['time'] + "] " + text
            self.item_status.get_child().set_text(text)
        # update list of recently changed files:
        while len(self.menu_log_list) < len(self.log_list):
            self.menu_log_list.append(Gtk.MenuItem(''))
        for (menu_item,log_entry) in zip(self.menu_log_list,self.log_list):
            menu_item.get_child().set_text("[" + log_entry['time'] + "] " + log_entry['text'])
        self.menu_log_list.show_all()
        # update list of recent errors:
        while len(self.menu_error_list) < len(self.error_list):
            self.menu_error_list.append(Gtk.MenuItem(''))
        for (menu_item,error) in zip(self.menu_error_list,self.error_list):
            menu_item.get_child().set_text("[" + error['time'] + "] " + error['text'])
        self.menu_error_list.show_all()

        return False # for GLib.idle_add


#def q(source):
#    print "Quit"
#def r(source):
#    print "Restart"
# 
#I = Indicator(r,q)
#Gtk.main()
# 
#while 1:  
#    line = readline()
#    print line.strip()

if __name__ == "__main__":
    # do some tests here
    print "Indicator.py started as a script"
