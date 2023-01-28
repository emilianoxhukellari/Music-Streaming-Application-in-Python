class Listener:
    """
    Summary:
    This class represents a class that is listening for events. It has a class property
    that contains all the listeners (objects).
    When a custom event occurs, if a listener is subscribed, its subscribed methods will be executed.

    Usage:
    Inherit Listener, and call self.listen('event_name', callback) for each event you want to listen.
    """

    listeners = []

    def __init__(self):
        self.listeners.append(self)
        self.listening_for = {}

    def listen(self, event_name: str, callback):
        """
        The listener calls this method to listen for an event. Pass event_name that you are listening for,
        and the callback method to be called when the event occurs. The method will be called from the Event
        thread.
        """

        self.listening_for[event_name] = callback


class Event:
    """
    Summary:
    This class represents an Event, which must have a name.

    Usage:
    Create an Event object to create an event. Pass self_fire=True to make it fire on initialization.
    Call self_fire if you do not pass self_fire=True to fire the event.
    Pass the event_name and all *args and **kwargs.
    """

    def __init__(self, event_name, *args, self_fire=False, **kwargs):
        self.event_name = event_name
        self.arguments = args
        self.kw_arguments = kwargs
        if self_fire:
            self.fire()

    def fire(self):
        """
        Call this method to fire the event.
        """

        for listener in Listener.listeners:
            if self.event_name in listener.listening_for:
                listener.listening_for[self.event_name](
                    *self.arguments, **self.kw_arguments
                )
