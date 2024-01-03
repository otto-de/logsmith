# collections.Callable has been moved to collections.abc.Callable in python 3.10+
import collections
import sys

if sys.version_info.major == 3 and sys.version_info.minor >= 10:
    collections.Callable = collections.abc.Callable
