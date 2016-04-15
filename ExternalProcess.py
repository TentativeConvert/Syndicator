#!/usr/bin/python
import os, signal, re, time, Queue
from subprocess import Popen, PIPE, STDOUT

ICONS_WORKING = ["network-transmit","network-receive"]#ubuntu-client-updating
ICON_WAITING =  "network-idle"    #ubuntuone-client-paused"
ICON_GOOD = "emblem-default"      #ubuntuone-client-idle
ICON_ERROR = "process-stop"       #ubuntuone-client-error

class Process():
    ABORTED_BY_USER = 143 
    # exit status returned by run() when process is aborted by user
    # 143 is the value returned by bash scripts when they are (immaturely) 
    # terminated by the user

    def __init__(self,command,output_queue,recognized_patterns):
        print "Initializing MySubProcess.Process object for command"
        print "    " + command
        self.command = command
        self.output_queue = output_queue
        self.process = None
        print recognized_patterns[0]
        self.patterns = [MessagePattern(pattern) for pattern in recognized_patterns]
        print "Process -- Recognized messages:"
        for m in self.patterns:
            m.show()

    def run(self):
        print "Process:  Starting"
        self.process = Popen(self.command, stdout=PIPE, stderr=STDOUT, close_fds=True, shell=True, preexec_fn=os.setsid)
        while 1:
            line = self.process.stdout.readline() 
            # The thread waits here until a line appears in the pipe.
            # Don't do anything with line before "if note line", not even line.strip()!
            if not line:
                # This happens exactly once, namely when the process ends.
                print "Subprocess has stopped feeding the pipe."
                break
            else: 
                smalllines = [l for ll in line.split('\n')  for l in ll.split('\r')]
                for l in smalllines:
                    print l.strip()     
                    self.__process_line(l.strip())
        if self.process:
            print "Waiting for exit status ..."
            streamdata = self.process.communicate()[0]
            exit_status = self.process.returncode
        else:
            exit_status = ABORTED_BY_USER            
        print " ... " + str(exit_status)
        return exit_status
        
    def abort(self):
        print "Process:  Aborting " + self.command
        if self.process:
            try: 
                os.killpg(self.process.pid, signal.SIGTERM)
                print "Subprocess has been terminated."            
            except OSError:
                print "Subprocess has already terminated."
        # Subsequently, the while loop in run() should break
        # and run() should return ABORTEY_BY_USER
        
    def __process_line(self,line):
        def add_to_queue(typ='status',text="",heading="",icon=""):
            self.output_queue.put({'type':typ,
                                'time':time.strftime("%H:%M"),
                                'text':text,'heading':heading,
                                'icon':icon})
        print "Process:  Processing line \n    %s" % line
        if line == "":
            return
        for p in self.patterns:
            match = p.pattern.match(line)
            if match:
                print "Process:  Detected match with %s" % str(p.pattern.pattern)
                status_text = match.expand(p.status_text)
                log_text = match.expand(p.log_text)
                error_text = match.expand(p.error_text)
                notify_heading = match.expand(p.notify_heading)
                icon = p.icon
                if status_text: 
                    add_to_queue(text=status_text,icon=icon)
                if error_text:
                    add_to_queue(typ='error',text=error_text)
                if log_text:
                    add_to_queue(typ='log',text=log_text)
                if notify_heading:
                    notify_text = match.expand(p.notify_text)
                    add_to_queue(typ='notify',text=notify_text,heading=notify_heading,icon=icon)
                return
        add_to_queue(text=line)



class MessagePattern():
    def __init__(self, array):
        if array.has_key('pattern'):
            self.pattern = re.compile(array['pattern'],re.I) #re.I means ignore case
        else:
            print "MessagePattern:  pattern keyword missing"
            # Raise Error here!
        # default values:
        self.status_text = r"\g<0>"
        self.log_text = ""
        self.error_text = ""
        self.notify_text = ""
        self.notify_heading = ""
        self.icon = ""
        # values specified by array:
        if array.has_key('status-text'):
            self.status_text = array['status-text']
        if array.has_key('log-text'):
            self.log_text = array['log-text']
        if array.has_key('error-text'):
            self.error_text = array['error-text']
        if array.has_key('notify-text'):
            self.notify_text = array['notify-text']
        if array.has_key('notify-heading'):
            self.notify_heading = array['notify-heading']
        if array.has_key('icon'):
            self.icon = array['icon']

    def show(self):
        print "    pattern: %s\n    log: %s\n    error: %s\n    notify: %s\n    heading:%s\n    icon:%s" % (str(self.pattern.pattern),self.log_text,self.error_text,self.notify_text,self.notify_heading,self.icon)


if __name__ == "__main__":
    # do some tests here
    print "ExternalProcess.py started as a script"
