# Created By: Virgil Dupras
# Created On: 2009-05-03
# Copyright 2015 Hardcoded Software (http://www.hardcoded.net)
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

from PyQt5.QtCore import Qt, QSettings, QRect, QObject, pyqtSignal, QStandardPaths
from PyQt5.QtWidgets import QDockWidget

from hscommon.trans import trget
from hscommon.util import tryint
from hscommon.plat import ISWINDOWS
from core.util import executable_folder

from os import path as op

tr = trget("qtlib")


def get_langnames():
    return {
        "cs": tr("Czech"),
        "de": tr("German"),
        "el": tr("Greek"),
        "en": tr("English"),
        "es": tr("Spanish"),
        "fr": tr("French"),
        "hy": tr("Armenian"),
        "it": tr("Italian"),
        "ja": tr("Japanese"),
        "ko": tr("Korean"),
        "nl": tr("Dutch"),
        "pl_PL": tr("Polish"),
        "pt_BR": tr("Brazilian"),
        "ru": tr("Russian"),
        "tr": tr("Turkish"),
        "uk": tr("Ukrainian"),
        "vi": tr("Vietnamese"),
        "zh_CN": tr("Chinese (Simplified)"),
    }


def normalize_for_serialization(v):
    # QSettings doesn't consider set/tuple as "native" typs for serialization, so if we don't
    # change them into a list, we get a weird serialized QVariant value which isn't a very
    # "portable" value.
    if isinstance(v, (set, tuple)):
        v = list(v)
    if isinstance(v, list):
        v = [normalize_for_serialization(item) for item in v]
    return v


def adjust_after_deserialization(v):
    # In some cases, when reading from prefs, we end up with strings that are supposed to be
    # bool or int. Convert these.
    if isinstance(v, list):
        return [adjust_after_deserialization(sub) for sub in v]
    if isinstance(v, str):
        # might be bool or int, try them
        if v == "true":
            return True
        elif v == "false":
            return False
        else:
            return tryint(v, v)
    return v


def create_qsettings():
    # Create a QSettings instance with the correct arguments.
    config_location = op.join(executable_folder(), "settings.ini")
    if op.isfile(config_location):
        settings = QSettings(config_location, QSettings.IniFormat)
        settings.setValue("Portable", True)
    elif ISWINDOWS:
        # On windows use an ini file in the AppDataLocation instead of registry if possible as it
        # makes it easier for a user to clear it out when there are issues.
        locations = QStandardPaths.standardLocations(QStandardPaths.AppDataLocation)
        if locations:
            settings = QSettings(op.join(locations[0], "settings.ini"), QSettings.IniFormat)
        else:
            settings = QSettings()
        settings.setValue("Portable", False)
    else:
        settings = QSettings()
        settings.setValue("Portable", False)
    return settings


# About QRect conversion:
# I think Qt supports putting basic structures like QRect directly in QSettings, but I prefer not
# to rely on it and stay with generic structures.


class Preferences(QObject):
    prefsChanged = pyqtSignal()

    def __init__(self):
        QObject.__init__(self)
        self.reset()
        self._settings = create_qsettings()

    def _load_values(self, settings, get):
        pass

    def get_rect(self, name, default=None):
        r = self.get_value(name, default)
        if r is not None:
            return QRect(*r)
        else:
            return None

    def get_value(self, name, default=None):
        if self._settings.contains(name):
            result = adjust_after_deserialization(self._settings.value(name))
            if result is not None:
                return result
            else:
                # If result is None, but still present in self._settings, it usually means a value
                # like "@Invalid".
                return default
        else:
            return default

    def load(self):
        self.reset()
        self._load_values(self._settings)

    def reset(self):
        pass

    def _save_values(self, settings, set_):
        pass

    def save(self):
        self._save_values(self._settings)
        self._settings.sync()

    def set_rect(self, name, r):
        if isinstance(r, QRect):
            rectAsList = [r.x(), r.y(), r.width(), r.height()]
            self.set_value(name, rectAsList)

    def set_value(self, name, value):
        self._settings.setValue(name, normalize_for_serialization(value))

    def saveGeometry(self, name, widget):
        # We save geometry under a 7-sized int array: first item is a flag
        # for whether the widget is maximized, second item is a flag for whether
        # the widget is docked, third item is a Qt::DockWidgetArea enum value,
        # and the other 4 are (x, y, w, h).
        m = 1 if widget.isMaximized() else 0
        d = 1 if isinstance(widget, QDockWidget) and not widget.isFloating() else 0
        area = widget.parent.dockWidgetArea(widget) if d else 0
        r = widget.geometry()
        rectAsList = [r.x(), r.y(), r.width(), r.height()]
        self.set_value(name, [m, d, area] + rectAsList)

    def restoreGeometry(self, name, widget):
        geometry = self.get_value(name)
        if geometry and len(geometry) == 7:
            m, d, area, x, y, w, h = geometry
            if m:
                widget.setWindowState(Qt.WindowMaximized)
            else:
                r = QRect(x, y, w, h)
                widget.setGeometry(r)
                if isinstance(widget, QDockWidget):
                    # Inform of the previous dock state and the area used
                    return bool(d), area
        return False, 0
