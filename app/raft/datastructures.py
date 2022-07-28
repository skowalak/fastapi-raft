import collections
from enum import Enum


class State(Enum):
    FOLLOWER = "FOLLOWER"
    CANDIDATE = "CANDIDATE"
    LEADER = "LEADER"


class ReplicatedLog(collections.UserList):
    """
    The replicated log Raft uses for cluster consensus

    Inherits
    --------
    collections.UserList
        A fancy way to say inherit from list (which is not possible)
    """

    pass
