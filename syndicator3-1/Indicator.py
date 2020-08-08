#!/usr/bin/python
# -*- coding: utf-8 -*-
########################## IMPORTS AND AUXILIARY CLASSES ###############################
import threading, collections 
import time, os.path
import gi ##NEW
gi.require_version("Gtk", "3.0") ##NEW
from gi.repository import Gtk, GObject, GLib
from gi.repository import AppIndicator3  # as AppIndicator
from gi.repository import Notify



class Indicator:
    """Panel icon and menu"""
    STATE_PAUSED = 0
    STATE_RUNNING = 1

    def __init__(self, function_restart, function_pause, function_quit, update_sleep_length=0.2,icon_paused="",icon_default=""): 
        self.appindicator = AppIndicator3.Indicator.new_with_path("unison-indicator", 
                                                                 "sync-default", 
                                                                 AppIndicator3.IndicatorCategory.SYSTEM_SERVICES,
                                                                 os.path.dirname(os.path.realpath(__file__)) + "/icons")
        self.appindicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        Notify.init("unison-indicator")
        self.notification = Notify.Notification.new("<b>Unison</b>","",None) # balloon notification
        # settings:
        self.update_sleep_length = update_sleep_length
        self.icon_paused = icon_paused
        self.icon_default = icon_default
        # internal data:
        self.status_list = collections.deque(maxlen=20)
        self.error_list = collections.deque(maxlen=10)
        self.file_list = collections.deque(maxlen=30)
        self.status_list_lock = threading.Lock()
        self.file_list_lock = threading.Lock()
        self.error_list_lock = threading.Lock()
        self.icon = ""
        self.notifytext = ""
        self.notifyheading = ""
        self.notifyicon = ""

        # Menu
        self.menu = Gtk.Menu()
        self.menu_file_list = Gtk.Menu()
        self.menu_error_list = Gtk.Menu()
        self.item_start   = Gtk.MenuItem('Restart')
        self.item_pause   = Gtk.MenuItem('Pause/abort')
        self.item_quit    = Gtk.MenuItem('Quit')
        self.item_file_list = Gtk.MenuItem('Recently changed files')
        self.item_error_list = Gtk.MenuItem('Error log')
        self.menu_file_list.append(Gtk.MenuItem('--'))
        self.menu_error_list.append(Gtk.MenuItem('--'))
        self.item_status = Gtk.MenuItem('')
        self.item_status.connect('activate',self.show_status_in_dialog)
        self.item_start.connect('activate', function_restart)
        self.item_pause.connect('activate', function_pause)
        self.item_quit.connect('activate', function_quit)
        self.item_file_list.set_submenu(self.menu_file_list)
        self.item_error_list.set_submenu(self.menu_error_list)
        menu_items = [self.item_status,
                      self.item_file_list,
                      self.item_error_list,
                      Gtk.SeparatorMenuItem(),
                      self.item_start,
                      self.item_pause,
                      self.item_quit]
        for item in menu_items:
            self.menu.append(item)
            self.appindicator.set_menu(self.menu)
        self.menu.show_all()

        # Auxiliary variables:
        self.icon_blink_counter = 0 
        self.update_event = threading.Event()
        self.update_thread = threading.Thread(target=self.__wait_for_updates)
        self.update_thread.daemon = True

        self.update_thread.start()
        self.new_status("Initializing ...")
        self.__set_state(Indicator.STATE_RUNNING)

    def start(self):
        self.__set_state(Indicator.STATE_RUNNING)

    def pause(self):
        self.__set_state(Indicator.STATE_PAUSED)
      
    def quit(self):
        print("Indicator:  Quitting.")
        Notify.uninit()

    def __set_state(self,state):
        """Sets state to 'Waiting' or 'Running' and updates menu accordingly."""
        self.state = state
        if state==Indicator.STATE_PAUSED:
            self.item_pause.hide()
            self.new_status("PAUSED")
            # icon muss manuell gesetzt werden 
            # da während STATE_PAUSED das Icon nicht aktuallisiert wird 
            GLib.idle_add(self.appindicator.set_icon,self.icon_paused)
        else:
            self.item_pause.show()
            self.new_status("RESTART",self.icon_default)
           
    def show_status_in_dialog(self,source):
        """Shows a message dialog displaying the full current status message;
           called when user clicks on the (shortened) status message in the panel menu"""        
        dialog = Gtk.MessageDialog(type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK, message_format="Back-in-time/unison report:")
        display_list = ["[%s] %s" % (entry['time'],entry['text']) for entry in reversed(self.status_list)]
        dialog.format_secondary_text("\n".join(display_list) + "\n\nFor further details, please consult the log-file.")
        dialog.run()
        dialog.destroy()
    
    def new_status(self,text,icon=None):
        self.status_list_lock.acquire()
        self.status_list.appendleft({'time':time.strftime("%H:%M"),'text':text})
        self.status_list_lock.release()
        if icon:
            self.icon = icon
        self.update_event.set()

    def new_file(self,text):
        # Remove older entries concerning the same file,
        # so that each file is listed at most once:
        self.file_list_lock.acquire()
        for entry in list(self.file_list):
            # list(...) is needed because file_list is mutated within the for loop
            if entry['text'] == text:
                self.file_list.remove(entry)
        self.file_list.appendleft({'time':time.strftime("%H:%M"),'text':text})
        self.file_list_lock.release()
        self.update_event.set()

    def new_error(self,text):
        self.error_list_lock.acquire()
        self.error_list.appendleft({'time':time.strftime("%H:%M"),'text':text})
        self.error_list_lock.release()
        self.update_event.set()


    def new_notification(self,text,heading=None,icon=None):
        if heading:
            self.notifyheading = heading
        if icon:
            extensions = ["svg","png"]
            for ext in extensions:
                testpath = os.path.dirname(os.path.realpath(__file__)) + "/icons/" + icon + "." + ext
                if os.path.isfile(testpath):
                    icon = testpath
                    break
            self.notifyicon = icon
        self.notifytext = text
        self.update_event.set()

    def __wait_for_updates(self):
        while True:
            self.update_event.wait()
            GLib.idle_add(self.__update_appearances)
            self.update_event.clear()
            time.sleep(self.update_sleep_length)

    def __update_appearances(self):
        #update notification:
        if self.notifytext != "":
            self.notification.update("<b>" + self.notifyheading + "</b>",self.notifytext,self.notifyicon)
            self.notification.show()
            self.notifytext = ""
        #update icon:
        if self.state == Indicator.STATE_RUNNING:
            icon_list = self.icon.split(",")
            no_of_icons = len(icon_list)
            if no_of_icons > 1:
                self.icon_blink_counter = (self.icon_blink_counter + 1) % no_of_icons
            else:
                self.icon_blink_counter = 0
            self.appindicator.set_icon(icon_list[self.icon_blink_counter])
        #update status text:
        self.status_list_lock.acquire()
        if self.status_list[0]:
            msg = self.status_list[0]
            text = msg['text']
            if len(text) > 50:
                text = text[:24] + "..." + text[-24:]
            text = "[" + msg['time'] + "] " + text
            self.item_status.get_child().set_text(text)
        self.status_list_lock.release()
        # update list of recently changed files:
        self.file_list_lock.acquire()
        while len(self.menu_file_list) < len(self.file_list):
            self.menu_file_list.append(Gtk.MenuItem(''))
        for (menu_item,filename) in zip(self.menu_file_list,self.file_list):
            menu_item.get_child().set_text("[" + filename['time'] + "] " + filename['text'])
        self.file_list_lock.release()
        self.menu_file_list.show_all()
        # update list of recent errors:
        self.error_list_lock.acquire()
        while len(self.menu_error_list) < len(self.error_list):
            self.menu_error_list.append(Gtk.MenuItem(''))
        for (menu_item,error) in zip(self.menu_error_list,self.error_list):
            menu_item.get_child().set_text("[" + error['time'] + "] " + error['text'])
        self.error_list_lock.release()
        self.menu_error_list.show_all()

        return False # for GLib.idle_add



if __name__ == "__main__":
    print("Running some tests with Indicator.py ...")
    import pdb

    def abort(self):
        print("Aborting ...")
    def quit(self):
        print("Quitting ...")
        Gtk.main_quit()
    def restart(self):
        print("Restarting ...")
    def test():
        i = 0
        rest = 0.01
        while True:
            time.sleep(rest)
            i = i+1
            I.new_status(text="status"+str(i),icon="sync1,sync2")
            time.sleep(rest)
            I.new_error(text="error"+str(i))
            time.sleep(rest)
            I.new_file(text="file"+str(i%5))
            time.sleep(rest)
            if (i%100)==66:
                I.new_status(text="error"+str(i),icon="sync-error")
                time.sleep(1)
            if (i%100)==99:
                #I.new_notification(text="This is a notification.",heading="Test",icon=os.path.abspath("icons/sync-good.svg"))
                I.new_notification(text="This is a notification.",heading="Test",icon="sync-good")
                time.sleep(5)

    I = Indicator(restart,abort,quit,1)
    test_thread = threading.Thread(target=test)
    test_thread.daemon = True
    test_thread.start()        
    Gtk.main()
        
