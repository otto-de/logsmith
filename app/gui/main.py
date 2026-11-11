import ctypes
import ctypes.util
import logging
import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from app.gui.gui import Gui

logger = logging.getLogger('logsmith')

NS_APPLICATION_ACTIVATION_POLICY_ACCESSORY = 1


def hide_dock_icon():
    if sys.platform != 'darwin':
        return
    try:
        objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library('objc'))
        ctypes.cdll.LoadLibrary(ctypes.util.find_library('AppKit'))
        objc.objc_getClass.restype = ctypes.c_void_p
        objc.objc_getClass.argtypes = [ctypes.c_char_p]
        objc.sel_registerName.restype = ctypes.c_void_p
        objc.sel_registerName.argtypes = [ctypes.c_char_p]

        send = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)(('objc_msgSend', objc))
        send_long = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long)(
            ('objc_msgSend', objc))

        ns_app = send(objc.objc_getClass(b'NSApplication'), objc.sel_registerName(b'sharedApplication'))
        send_long(ns_app, objc.sel_registerName(b'setActivationPolicy:'), NS_APPLICATION_ACTIVATION_POLICY_ACCESSORY)
    except Exception:
        logger.warning('could not hide dock icon', exc_info=True)


def start_gui():
    try:
        app = QApplication(sys.argv)
        hide_dock_icon()
        app.setQuitOnLastWindowClosed(False)
        Gui(app)

        timer = QTimer()
        timer.timeout.connect(lambda: None)
        timer.start(100)

        sys.exit(app.exec())
    except Exception:
        logging.error('unexpected error', exc_info=True)
