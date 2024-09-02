import time
import threading
class pcs:
    def __init__(self):
        self.name = "transmission"
        self.abort = False
    def unlimited(self):
        while not self.abort:
            print("Im running")
            time.sleep(2)
        print("stopped running")


if __name__ == '__main__':
    p1 = pcs()
    t = threading.Thread(target= p1.unlimited)
    t.start()
    while True : 
        cmd = input("enter quit if you want to exit")
        if cmd == 'quit':
            p1.abort = True
            t.join()
            break