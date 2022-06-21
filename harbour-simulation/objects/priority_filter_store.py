import simpy
from simpy.core import BoundClass


class MyPriorityFilterStoreGet(simpy.resources.base.Get):
    """Extension of SimPy get request, adding priority and filtering."""

    def __init__(self, resource, priority=0, filter=lambda item: True):
        """Initializes the class.

        :param <resource>: simpy resource to get
        :param <priority>: priority of the request (0: default)
        :param <filter>: lambda function for filtering objects
        """

        # Priority of the request (smaller -> more important)
        self.priority = priority

        # Set lambda function as filter
        self.filter = filter

        # The time at which the request was made
        self.time = resource._env.now

        # The time at which the request succeeded
        self.usage_since = None

        # Key for sorting events
        self.key = (self.priority, self.time)

        super().__init__(resource)

class MyPriorityFilterStore(simpy.resources.store.FilterStore):
    """Extension of SimPy FilterStore, overwriting get request."""
    
    GetQueue = simpy.resources.resource.SortedQueue
    get = BoundClass(MyPriorityFilterStoreGet)