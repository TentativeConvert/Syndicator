#!/usr/bin/python
import os, signal, re, time
from subprocess import Popen, PIPE, STDOUT

class ExternalProcess():
    ABORTED_BY_USER = 143 
    # exit status returned by run() when process is aborted by user
    # 143 is the value returned by bash scripts when they are (immaturely) 
    # terminated by the user

    def __init__(self,command,recognized_patterns,report_status,report_error,report_file,report_notification,icon_working=""):
        print("Initializing MySubProcess.Process object for command")
        print("    " + command)
        self.command = command
        self.icon_working = icon_working
        # call-back functions:
        self.report_status = report_status
        self.report_error = report_error
        self.report_file = report_file
        self.report_notification = report_notification

        self.process = None
        print(recognized_patterns[0])
        self.patterns = [MessagePattern(pattern) for pattern in recognized_patterns]
        print("Process -- Recognized messages:")
        for m in self.patterns:
            m.show()

    def run(self):
        print("Process:  Starting")
        self.process = Popen(self.command, stdout=PIPE, stderr=STDOUT, close_fds=True, shell=True, preexec_fn=os.setsid)
        while 1:
            line = self.process.stdout.readline() 
            # The thread waits here until a line appears in the pipe.
            # Don't do anything with line before "if note line", not even line.strip()!
            if not line:
                # This happens exactly once, namely when the process ends.
                print("Subprocess has stopped feeding the pipe.")
                break
            else: 
                smalllines = [l for ll in line.split('\n')  for l in ll.split('\r')]
                for l in smalllines:
                    print(l.strip())     
                    self.__process_line(l.strip())
        if self.process:
            print("Waiting for exit status ...")
            streamdata = self.process.communicate()[0]
            exit_status = self.process.returncode
        else:
            exit_status = ABORTED_BY_USER            
        print(" ... " + str(exit_status))
        return exit_status
        
    def abort(self):
        print("Process:  Aborting " + self.command)
        if self.process:
            try: 
                os.killpg(self.process.pid, signal.SIGTERM)
                print("Subprocess has been terminated.")            
            except OSError:
                print("Subprocess has already terminated.")
        # Subsequently, the while loop in run() should break
        # and run() should return ABORTEY_BY_USER
        
    def __process_line(self,line):
        #print "Process:  Processing line \n    %s" % line
        if line == "":
            return
        for p in self.patterns:
            match = p.pattern.match(line)
            if match:
                print("Process:  Detected match with %s" % str(p.pattern.pattern))
                status_text = match.expand(p.status_text)
                file_text = match.expand(p.file_text)
                error_text = match.expand(p.error_text)
                notify_heading = match.expand(p.notify_heading)
                icon = p.icon
                if status_text: 
                    self.report_status(status_text,icon)
                if error_text:
                    self.report_error(error_text)
                if file_text:
                    self.report_file(file_text)
                if notify_heading:
                    notify_text = match.expand(p.notify_text)
                    self.report_notification(text=notify_text,heading=notify_heading,icon=icon)
                return
        self.report_status(line,self.icon_working)

class MessagePattern():
    def __init__(self, array):
        if 'pattern' in array:
            self.pattern = re.compile(array['pattern'],re.I) #re.I means ignore case
        else:
            print("MessagePattern:  pattern keyword missing")
            # Raise Error here!
        # default values:
        self.status_text = r"\g<0>"
        self.file_text = ""
        self.error_text = ""
        self.notify_text = ""
        self.notify_heading = ""
        self.icon = ""
        # values specified by array:
        if 'status-text' in array:
            self.status_text = array['status-text']
        if 'file-text' in array:
            self.file_text = array['file-text']
        if 'error-text' in array:
            self.error_text = array['error-text']
        if 'notify-text' in array:
            self.notify_text = array['notify-text']
        if 'notify-heading' in array:
            self.notify_heading = array['notify-heading']
        if 'icon' in array:
            self.icon = array['icon']

    def show(self):
        print(r"""*** PATTERN %s ***
status-text:    %s
file-text:      %s    
error-text:     %s    
notify-text:    %s    
notify-heading: %s    
icon:%s""" % (str(self.pattern.pattern),self.status_text,self.file_text,self.error_text,self.notify_text,self.notify_heading,self.icon))





if __name__ == "__main__":
    print("Running some tests with ExternalProcess.py.")
    from .tests import dummyconfig as config
    import threading

    def report_status(text,icon):
        print("STATUS %s, ICON %s" % (text,icon))
    def report_file(text):
        print("FILE %s" % text)
    def report_error(text):
        print("ERROR %s" % text)
    def report_notification(text,heading,icon):
        print("NOTIFICATION %s, HEADING %s, ICON %s" % (text,heading,icon))

    P = ExternalProcess(command=config.sync_command,
                        recognized_patterns=config.sync_patterns,
                        report_status = report_status,
                        report_file = report_file,
                        report_error = report_error,
                        report_notification = report_notification,
                        icon_working = config.sync_icon_working)

    def test_run():
        P.run()
    test_thread = threading.Thread(target=test_run)
    test_thread.start()
    time.sleep(2)
    P.abort()
    test_thread.join()

    

