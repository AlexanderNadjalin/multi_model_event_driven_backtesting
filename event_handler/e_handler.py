import queue

from event_handler import event as ev


class EventHandler:
    """
    Class for handling events.
    """
    def __init__(self,
                 verbose=False):
        """
        Create empty queue.
        :param verbose: Bool.
        """
        self.event_queue = queue.Queue()
        self.verbose = verbose

    def put_event(self,
                  event: ev) -> None:
        """
        Put an event in the queue.
        :param event: Event object.
        :return: None.
        """
        self.event_queue.put(event)

    def get_event(self) -> ev:
        """
        Get and remove next event from the queue.
        :return: None.
        """
        return self.event_queue.get()

    def is_empty(self) -> bool:
        """
        Check if queue is empty.
        :return: Bool.
        """
        return self.event_queue.empty()

    def done(self) -> None:
        """
        Previous enqueued task is completed.
        :return: None
        """
        self.event_queue.task_done()
