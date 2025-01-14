import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap, QColor

script_dir = os.path.dirname(os.path.realpath(__file__))

ICON_STYLE_FULL = 'full'
ICON_STYLE_OUTLINE = 'outline'
ICON_STYLE_ERROR = 'error'
ICON_STYLE_BUSY = 'busy'
ICON_STYLE_GCP = 'gcp'


class Assets:
    def __init__(self):
        self.cloud = self._resource_path('assets/cloud.svg')
        self.cloud_outline = self._resource_path('assets/cloud-outline.svg')
        self.cloud_busy = self._resource_path('assets/cloud-busy.svg')
        self.cloud_google = self._resource_path('assets/google-cloud.svg')
        self.bug = self._resource_path('assets/bug.svg')
        self.standard = self.get_icon()

    def get_icon(self, style=ICON_STYLE_FULL, color_code='#FFFFFF'):
        if style == ICON_STYLE_OUTLINE:
            return self._color_icon(self.cloud_outline, color_code)
        if style == ICON_STYLE_ERROR:
            return self._color_icon(self.bug, color_code)
        if style == ICON_STYLE_GCP:
            return self._color_icon(self.cloud_google, color_code)
        if style == ICON_STYLE_BUSY:
            return self._color_icon(self.cloud_busy, color_code)
        else:
            return self._color_icon(self.cloud, color_code)

    @staticmethod
    def _color_icon(icon, color_code):
        pix_map = QPixmap(icon)
        mask = pix_map.createMaskFromColor(QColor('black'), Qt.MaskMode.MaskOutColor)
        pix_map.fill(QColor(color_code))
        pix_map.setMask(mask)
        return QIcon(pix_map)

    @staticmethod
    def _resource_path(relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath('.'), f'{script_dir}/../{relative_path}')
