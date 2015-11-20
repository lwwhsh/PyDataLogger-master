__author__ = 'root'
import multiprocessing

def producer(ns, event):
    #ns.value = 'This is the value'
    ns.value = {'a':[1,2,3,4,5,6], 'b':['a','b','c','d'], 'c':list(range(10))}
    event.set()

def consumer(ns, event):
    try:
        value = ns.value
    except Exception, err:
        print 'Before event, consumer got:', str(err)
    event.wait()
    print 'After event, consumer got:', ns.value

if __name__ == '__main__':
    mgr = multiprocessing.Manager()
    namespace = mgr.Namespace()
    event = multiprocessing.Event()
    p = multiprocessing.Process(target=producer, args=(namespace, event))
    c = multiprocessing.Process(target=consumer, args=(namespace, event))

    c.start()
    p.start()

    c.join()
    p.join()