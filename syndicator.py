#!/usr/bin/python
########################## IMPORTS AND AUXILIARY CLASSES ###############################
import os, threading, signal, collections, re, more_itertools
import time
import Queue
from subprocess import Popen, PIPE, STDOUT
from gi.repository import Gtk, GObject, GLib
from gi.repository import AppIndicator3 as AppIndicator
from gi.repository import Notify

class MessagePattern():
    def __init__(self,pattern,icon=None, statustext=r"\g<0>", notify=False, notifyicon="", notifyheading="", notifytext="", filelisttext="", terminate=False):
        self.pattern = re.compile(pattern,re.I) #re.I means ignore case
        self.icon = icon
        self.statustext = statustext
        self.notify = notify
        self.notifyicon = notifyicon
        self.notifyheading = notifyheading
        self.notifytext = notifytext
        self.filelisttext = filelisttext
        self.terminate = terminate
    def show(self):
        txt = self.pattern.pattern + "\n   -->"
        if self.icon: txt = txt + self.icon
        print txt
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
         
# KNOWN MESSAGES
ICONS_WORKING = ["network-transmit","network-receive"]#ubuntu-client-updating
ICON_WAITING =  "network-idle"    #ubuntuone-client-paused"
ICON_GOOD = "emblem-default"      #ubuntuone-client-idle
ICON_ERROR = "process-stop"       #ubuntuone-client-error
END_OF_SUBPROCESS = "UNISON-WRAPPER: Subprocess has terminated"
PATTERNS = []
#PATTERNS.append(MessagePattern(pattern=r"(Alles Ok)",icon=ICON_GOOD,notifyheading=r"\1",notifytext=r"Did you know that?"))
#PATTERNS.append(MessagePattern(pattern=r"(Fehler)",icon=ICON_ERROR,notifyheading=r"\1",notifytext=r"\1"))
#PATTERNS.append(MessagePattern(pattern=r"(Keine Verbindung)",icon=ICON_ERROR,notifyheading=r"\1",notifytext=r"\1"))
#PATTERNS.append(MessagePattern(pattern=r"(\d+).*(Keine Nachricht)",filelisttext=r"\1"))
#PATTERNS.append(MessagePattern(pattern=r"(A)",icon=ICON_GOOD,notifyheading=r"\1",notifytext=r"Did you know that?"))
#PATTERNS.append(MessagePattern(pattern=r"B",icon=ICON_ERROR))
#PATTERNS.append(MessagePattern(pattern=r"F",icon="gtk-home"))
PATTERNS.append(MessagePattern(pattern=r"\[END\]\s+Updating file\s+(.*/)*([^/]+)", 
                               filelisttext=r" \2"))
PATTERNS.append(MessagePattern(pattern=r"\[END\]\s+Copying\s+(.*/)*([^/]+)", 
                               filelisttext=r"*\2"))
PATTERNS.append(MessagePattern(pattern=r"\[END\]\s+Deleting\s+(.*/)*([^/]+)", 
                               filelisttext=r"[\2]"))
PATTERNS.append(MessagePattern(pattern=r"(Synchronization complete).* \((\d+[^)]*)\)", 
                               notifyheading=r"\1",
                               notifytext=r"\2",
                               icon=ICON_GOOD))
PATTERNS.append(MessagePattern(pattern=r"(Nothing to do: .*)",
                               icon=ICON_GOOD))
PATTERNS.append(MessagePattern(pattern=r"(Fatal error): (.*)",
                               notifyheading=r"\1",
                               notifytext=r"\2",
                               icon=ICON_ERROR))
PATTERNS.append(MessagePattern(pattern=r"(Error): (.*)",
                               notifyheading=r"\1",
                               notifytext=r"\2",
                               icon=ICON_ERROR))
PATTERNS.append(MessagePattern(pattern=r"(Error) (.*)",
                               notifyheading=r"\1",
                               notifytext=r"\g<0>",
                               icon=ICON_ERROR))
PATTERNS.append(MessagePattern(pattern=r"File name too long",
                               notifyheading=r"Error",
                               notifytext=r"\g<0>",
                               icon=ICON_ERROR))
PATTERNS.append(MessagePattern(pattern=END_OF_SUBPROCESS,
                               statustext="",
                               terminate=True))
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
        self.statuslist = collections.deque(maxlen=30)
        self.filelist = collections.deque(maxlen=30)

        self.known_messages = PATTERNS
        #print "Known messages:"
        #for m in self.known_messages:
        #    m.show()

        self.icons_working = ICONS_WORKING
        self.icon_waiting = ICON_WAITING

        def build_menu():
            self.menu = Gtk.Menu()
            self.menu_filelist = Gtk.Menu()

            self.item_start   = Gtk.MenuItem('Start ...')
            self.item_quit    = Gtk.MenuItem('Quit')
            self.item_filelist = Gtk.MenuItem('Recently changed files')
            self.menu_filelist.append(Gtk.MenuItem('--'))
            self.item_status = Gtk.MenuItem('')
            self.item_status.connect('activate',self.show_status_in_dialog)
            self.item_start.connect('activate', self.wrapper.restart)
            self.item_quit.connect('activate', self.wrapper.quit)
            self.item_filelist.set_submenu(self.menu_filelist)
            
            menu_items = [self.item_filelist,self.item_status,Gtk.SeparatorMenuItem(),self.item_start,self.item_quit]
            for item in menu_items:
                self.menu.append(item)
            self.appindicator.set_menu(self.menu)
            self.statuslist.appendleft("[No process started]")
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
        dialog = Gtk.MessageDialog(type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK, message_format="Back-in-time/unison report:")
        dialog.format_secondary_text(">> "+"\n>> ".join(reversed(self.statuslist)) + "\n\nFor further details, please consult the log-file.")
        dialog.run()
        dialog.destroy()
    
    def add_message_to_queue(self,message):
        self.message_queue.put(message)   
        
    def __watch_message_queue(self):
    # main process of this class;
    # runs indefinitly in a separate thread self.watch_thread
    # The main difficulty is to catch the message when the "subprocesses have terminated"
    # and display the _previous_ message in this case:
        class TempData: pass
        def process_message(msg,temp):
            msg = msg.strip()
            if msg == "":
                return temp
            print "processing " + msg
            for p in self.known_messages:
                m = p.pattern.match(msg)
                if m:
                    print "MATCH with " + str(p.pattern.pattern)
                    temp.terminate = p.terminate
                    temp.icon = p.icon
                    st = m.expand(p.statustext)
                    flt = m.expand(p.filelisttext)
                    nh = m.expand(p.notifyheading)
                    if st: self.statuslist.appendleft(st)
                    if flt: 
                        self.filelist.appendleft(flt)
                        self.filelist = collections.deque(list(more_itertools.unique_everseen(self.filelist)),maxlen = self.filelist.maxlen)
                    if nh: 
                        temp.notifyheading = nh
                        temp.notifytext = m.expand(p.notifytext)
                        temp.notifyicon = p.icon
                    #print "-> groups: " + ", ".join(m.groups())
                    #print "-> notify-heading: " + temp.notifyheading + " [" + p.notifyheading + "]"
                    #print "-> notify-text: " + temp.notifytext + " [" + p.notifytext + "]"
                    #print "-> log: " + m.expand(p.filelisttext)
                    return temp
            # Unknown messages are added to menu without any alterations.
            # The only known message that currently appears only in altered form in the menu
            # is the "end of process" --- it does not appear at all.
            self.statuslist.appendleft(msg)
            return temp

        def process_queue(q,temp):
            msg = q.get(block=True)
            temp = process_message(msg,temp)
            q.task_done()
            try:
                while True:
                    msg = q.get(block=False) 
                    temp = process_message(msg,temp)
                    q.task_done()                  
            except Queue.Empty:
                return temp
            return temp# this line should never be reached, but the interpreter wants it here

        while True:
            temp = TempData()
            temp.terminate = False
            temp.icon = None
            temp.notifyheading = ""
            temp.notifytext = ""
            temp.notifyicon = None
            temp = process_queue(self.message_queue,temp)
            GLib.idle_add(self.__update_appearances,temp.icon,temp.notifyheading,temp.notifytext,temp.notifyicon)
            if temp.terminate:
                GLib.idle_add(self.wrapper.stop, None)
            time.sleep(0.2)

    def __update_appearances(self,icon=None,notifyheading="",notifytext="",notifyicon=None):
        #update notification:
        if not notifyheading == "":
            self.notification.update("<b>" + notifyheading + "</b>",notifytext,notifyicon)
            self.notification.show()
        #update icon:
        if self.state == STATE_RUNNING:
            if not icon:
                try: 
                    self.blink_counter = (self.blink_counter + 1) % len(self.icons_working)
                except AttributeError: self.blink_counter = 0 
                icon = self.icons_working[self.blink_counter]
            self.appindicator.set_icon(icon)
        #update status messages:
        if self.statuslist[0]:
            msg = self.statuslist[0]
            if len(msg) > 50:
                msg = msg[:24] + "..." + msg[-24:]
            msg = "[" + time.strftime("%H:%M") + "] " + msg
            self.item_status.get_child().set_text(msg)
        # update list of recently changed files:
        while len(self.menu_filelist) < len(self.filelist):
            self.menu_filelist.append(Gtk.MenuItem(''))
        for (menu_item,f) in zip(self.menu_filelist,self.filelist):
            menu_item.get_child().set_text(f)
        self.menu_filelist.show_all()
        return False # for GLib.idle_add
        
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
                smalllines = [l for ll in line.split('\n')  for l in ll.split('\r')]
                for l in smalllines:
                    self.indicator.add_message_to_queue(l.strip())
                

print "Hello."
GObject.threads_init()
UnisonWrapper().main()
print "Good bye."
