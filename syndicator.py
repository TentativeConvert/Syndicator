#!/usr/bin/python
##################################  SETTINGS  ########################################
# LIST OF COMMANDS executed, 
# given as a list of tuples of the form (description, command).
# The opening dialog displays this list.
COMMANDS = (
    ("Backup all files", "backintime --profile-id 2 -b"), 
    ("Run unison once with -backup option", "unison XPS12-reh -backup 'Name *'"),
    ("Run unison with -watch option","unison XPS12-reh -repeat watch"),
#    ("Dummy","~/Scripts/dummy.sh"),
#    ("Dummywatch","~/Scripts/dummywatch.sh"),
    )
# Some of the commands are selected by default in the opening dialog:
DEFAULTS = [
    (True, False, True),   # all commands are selected initially
    (None, False, None)   # at the first /re/start, first command is deselected
    ]
         
# ICONS SHOWN IN THE PANEL
# (1) icons associated with important messages:
#     ICONS_MESSAGES is a list of tuples in the format
#       ([msg1, msg2, ...], icon),
#     where msg1, msg2, ... are the messages from backintime/unison/... associated with icon
# (2) icons indicating normal operation:
#     when output from backintime/unison/... does not match any of the above messages,
#     the panel icon simply iterates over the icons in ICONS_WORKING
# (3) when waiting for user input, ICON_WAITING is shown
ICONS_MESSAGES = (
    (["Alles OK","Synchronization complete","Nothing to do: replicas have not changed"],
     "emblem-default"
    ),
    (["Fehler",
      "Keine Verbindung",
      "Fatal error: Lost connection with the server"],
     "process-stop"
    )
)
ICONS_WORKING = ["network-transmit","network-receive"]
ICON_WAITING =  "network-transmit-receive"
END_OF_SUBPROCESS = "UNISON-WRAPPER: Subprocess has terminated"
########################## IMPORTS AND AUXILIARY CLASSES ###############################
import os, threading, signal
import time
import Queue
from subprocess import Popen, PIPE, STDOUT
from gi.repository import Gtk, GObject, GLib
from gi.repository import AppIndicator3 as AppIndicator
from gi.repository import Notify
############################### ACTUAL PROGRAM #########################################
# PROGRAM STATES:
# (A) Waiting
#     - at the beginning
#     - each time the user clicks restart
#     No background processes are running in this state.
#     The "opening dialog" is displayed, and the panel menu has few entries.
# (B) Running
#     The commands selected (backintime, unison ...) are running in the background.
#     The "opening dialog is hidden"
#     The panel menu displays output from backintime/unison ...  and updates icon accordingly
STATE_WAITING = 0
STATE_RUNNING = 1

# CLASSES:
# (1) MyIndicator:  Panel icon and menu
#     initializes a separate thread that constantly watches a "message queue"
# (2) OpeningDialog:  Opening dialog
# (3) UnisonWrapper:  The main classes, managing calls to unison etc.
#     manages a separate thread that watches the stdout pipe of unison/... 
#     and piles adds the output to the "message queue" of (1)

class MyIndicator:
    """Panel icon and menu"""
    def __init__(self, wrapper):
        self.appindicator = AppIndicator.Indicator.new("unison-indicator", Gtk.STOCK_INFO, AppIndicator.IndicatorCategory.SYSTEM_SERVICES)
        self.appindicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        Notify.init("unison-indicator")
        self.notification = Notify.Notification.new("<b>Unison</b>","",None) # balloon notification
        self.wrapper = wrapper
        self.icons_messages = tuple(
            ([self.__standardize(message) for message in message_list],icon)
            for message_list,icon in ICONS_MESSAGES)
        print "Known messages:"
        print "\n".join(["  " + "\n  ".join(message_list) + "\n  -> icon: " + icon
            for message_list,icon in self.icons_messages])
        self.icons_working = ICONS_WORKING
        self.icon_waiting = ICON_WAITING
        def build_menu():
            self.item_start   = Gtk.MenuItem('Start ...')
            self.item_quit    = Gtk.MenuItem('Quit')
            self.item_sep     = Gtk.SeparatorMenuItem()
            self.item_status =  Gtk.MenuItem('[No processes started.]')
            self.item_start.connect('activate', self.wrapper.restart)
            self.item_status.connect('activate',self.show_status_in_dialog)
            self.item_quit.connect('activate', self.wrapper.quit)
            self.menu = Gtk.Menu()
            self.appindicator.set_menu(self.menu)
            self.status_message = "Please select processes to start in the main dialog."
            menu_items = [self.item_start,self.item_quit,self.item_sep,self.item_status]
            for item in menu_items:
                self.menu.append(item)
            self.menu.show_all()
        build_menu()
        self.set_state(STATE_WAITING) 
        self.message_queue = Queue.Queue() 
        self.watch_thread = threading.Thread(target=self.__watch_message_queue)
        self.watch_thread.daemon = True
        self.watch_thread.start()
                
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
        dialog = Gtk.MessageDialog(type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK, message_format=self.status_message)
        dialog.format_secondary_text("For further details please consult the log-file.")
        dialog.run()
        dialog.destroy()
    
    def add_message_to_queue(self,message):
        self.message_queue.put(message)   
        
    def __watch_message_queue(self):
    # main process of this class;
    # runs indefinitly in a separate thread self.watch_thread
    # The main difficulty is to catch the message when the "subprocesses have terminated"
    # and display the _previous_ message in this case:
        def get_last_item_in(q):
            last_val = q.get(block=True)
            prev_val = None
            q.task_done()
            try:
                while True:
                    temp = q.get(block=False) 
                    prev_val = last_val
                    last_val = temp
                    q.task_done()                  
            except Queue.Empty:
                return (last_val,prev_val)
        while True:          
            (last_msg,prev_msg) = get_last_item_in(self.message_queue)
            if last_msg == END_OF_SUBPROCESS:
                msg = prev_msg
                terminate = True
            else:
                msg = last_msg
                terminate = False
            if msg: self.__update_status(msg)
            if terminate: GLib.idle_add(self.wrapper.stop, None)
            time.sleep(0.2)
            
    def __update_status(self,msg):
        # for the use of GLib.idle_add in this function, see
        # wiki.gnome.org/Projects/PyGObject/Threading
        def update_icon(icon):
            if self.state == STATE_RUNNING:
                self.appindicator.set_icon(icon)
            return False
        def update_status_display(text):
            if len(text) > 50:
                text = text[0:48] + " ..."
            text = "[" + time.strftime("%H:%M") + "] " + text
            print "Status:  " +  text
            self.item_status.get_child().set_text(text)
            return False
        def update_notification(text,icon):
            self.notification.update("<b>Unison</b>",text,icon)
            self.notification.show()
            return False
        def find_relevant_message():
            sss = self.__standardize(msg)
            for message_list,icon in self.icons_messages:
                for message in message_list:
                    if sss == message:
                        GLib.idle_add(update_icon,icon)
                        GLib.idle_add(update_notification,msg,icon)
                        return True 
            return False
        # update status message in last menu item:
        GLib.idle_add(update_status_display,msg)
        # update icon:
        if not find_relevant_message():
            try: self.blink_counter = (self.blink_counter + 1) % len(self.icons_working)
            except AttributeError: self.blink_counter = 0 
            GLib.idle_add(update_icon,self.icons_working[self.blink_counter])
 
    
    def __standardize(self,message):
        # I shorten and upper-case the messages in ICONS_MESSAGES
        # and the status messages coming from unison.
        return message[0:20].lower()    
       
class OpeningDialog(Gtk.Window):
    """Opening dialog"""
    def __init__(self, wrapper):
        PADDING = 10
        self.wrapper = wrapper
        
        Gtk.Window.__init__(self,title="Unison-Wrapper")
        self.set_border_width(PADDING)
        self.label  = Gtk.Label.new("The following commands will be executed:")
        self.checks = []
        for descr,cmd in wrapper.commands:
            check_button =  Gtk.CheckButton.new_with_mnemonic(descr + " (" + cmd + ")")
            self.checks.append(check_button)
             
        self.button_run = Gtk.Button.new_with_mnemonic("_Start!")
        self.button_run.connect("clicked", self.__run_commands)        
        self.connect("delete_event", self.hide_window)
               
        self.bigbox = Gtk.Box(orientation=1, spacing=0)
        self.checksbox = Gtk.Box(orientation=1, spacing=0)
        
        self.add(self.bigbox)
        self.bigbox.pack_start(child=self.label,     expand=True, fill=True,  padding=0)
        self.bigbox.pack_start(child=self.checksbox, expand=True, fill=False, padding=PADDING)
        for ch in self.checks:
            self.checksbox.pack_start(child=ch, expand=True, fill=True,  padding=0)
        self.bigbox.pack_start(child=self.button_run,     expand=True, fill=True,  padding=0)
       
    def set_defaults(self,defaults):
       if defaults:
            for checkbox,val in zip(self.checks,defaults):
                if val != None: checkbox.set_active(val)                    
        
    def show_window(self,data=None):
        self.set_position(1) # display at center of screen
        self.show_all()
        self.button_run.grab_focus()
        self.present()       # in case windows was already open but got covered
        
    def hide_window(self,source=None,data=None):
        self.hide()
        return True # for delete event
        
    def __run_commands(self,source):
        self.hide()
        self.wrapper.run([checkbox.get_active() for checkbox in self.checks])        

class UnisonWrapper:
    def __init__(self):
        self.commands = COMMANDS    
        self.defaults = DEFAULTS
        self.dialog = OpeningDialog(self)
        self.dialog.set_defaults(self.defaults.pop(0))
        
        self.indicator = MyIndicator(self)
        self.process = None
        self.thread = None
        
    def main(self):
        self.dialog.show_window()
        Gtk.main()
        
    def run(self,options):
        if self.defaults: # because of "pop" in next line, the list of lists of default values will be empty after the second run
            self.dialog.set_defaults(self.defaults.pop(0)) 
        self.indicator.set_state(STATE_RUNNING)
        command_line = "(" + " && ".join([cmd[1] for cmd,val in zip(self.commands,options) if val]) + ")" 
        # The parentheses around the list of commands are important.
        # Without the parentheses, stdout of the first command(s) get(s) lost.
        print "Calling the following command in a subprocess: \n  " + "  " + command_line
        self.process = Popen(command_line, stdout=PIPE, stderr=STDOUT, close_fds=True, shell=True, preexec_fn=os.setsid)
        self.thread = threading.Thread(target=self.watch_pipe, args=(self.process.stdout,))
        self.thread.daemon = True
        self.thread.start()

    def stop(self,source):
        self.indicator.set_state(STATE_WAITING)
        if self.process:
            os.killpg(self.process.pid, signal.SIGTERM)
            self.process = None
            print "Subprocess has been terminated."            
        if self.thread:
            if self.thread.isAlive():
                self.thread.join()
                print "Subthread has joined main thread."
            self.thread = None 

    def restart(self,source):
        self.stop(source)
        self.dialog.show_window()

    def quit(self, source):
        self.stop(source) 
        Notify.uninit()
        Gtk.main_quit()
        print "Gtk has quit."

#    @staticmethod
    def watch_pipe(self, pipe): 
        while 1:  
            line = pipe.readline() 
            # The thread waits here until a line appears in the pipe.
            # Don't do anything with line before "if note line", not even line.strip()!
            if not line:
                # This happens exactly once, namely when the process ends.
                self.indicator.add_message_to_queue(END_OF_SUBPROCESS)
                print "Subprocess has stopped feeding the pipe."
                break
            else: 
                self.indicator.add_message_to_queue(line.strip())
                

print "Hello."
GObject.threads_init()
UnisonWrapper().main()
print "Good bye."
