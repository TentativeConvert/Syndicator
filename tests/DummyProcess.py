#!/usr/bin/python
import Queue, time

class Sync():
    def __init__(self,out_queue):
        print "DummySync:  Initializing ..."
        self.out_queue = out_queue
        self.aborted = True
        
    def run(self):
        print "DummySync:  Running ..."
        self.aborted = False
        while self.aborted == False:
            self.__add_to_queue(typ='error',text='I stumbled upon an error.')
            time.sleep(1)
            self.__add_to_queue(text='I am healthy.')
            time.sleep(1)
            self.__add_to_queue(typ='notification',
                                heading='Balloons',
                                text='Balloons are nice.',
                                icon='ubuntuone-client-idle')
            time.sleep(1)
            self.__add_to_queue(typ='log',text='Did I update a file?')
            time.sleep(5)

    def abort(self):
        print "DummySync:  Aborting ..."
        self.aborted = True
        return 143

    def __add_to_queue(self,typ="status",text="",heading="",icon=""):
        self.out_queue.put({'type':typ,'time':time.strftime("%H:%M"),'text':text,'heading':heading,'icon':icon})
        

#q = Queue.Queue()
#Test = Sync(q)
#Test.run()

