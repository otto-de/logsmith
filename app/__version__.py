__version__ = (9, 1, 0)
__prerelease__ = 'rc.1'

__version_string__ = '.'.join(str(i) for i in __version__)
if __prerelease__:
    __version_string__ = f'{__version_string__}-{__prerelease__}'
