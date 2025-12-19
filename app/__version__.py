__version__ = (9, 0, 2)
__prerelease__ = None

__version_string__ = '.'.join(str(i) for i in __version__)
if __prerelease__:
    __version_string__ = f'{__version_string__}-{__prerelease__}'
