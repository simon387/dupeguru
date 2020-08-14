# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

from PyQt5.QtCore import Qt, QModelIndex, pyqtSignal
from PyQt5.QtGui import QBrush, QFont, QFontMetrics, QColor
from PyQt5.QtWidgets import QTableView

from qtlib.column import Column
from qtlib.table import Table


class ExcludeListTable(Table):
    """Model for exclude list"""
    COLUMNS = [
        Column("marked", defaultWidth=15),
        Column("regex", defaultWidth=230)
    ]

    def __init__(self, app, view, **kwargs):
        model = app.model.exclude_list_dialog.exclude_list_table  # pointer to GUITable
        super().__init__(model, view, **kwargs)
        view.horizontalHeader().setSortIndicator(1, Qt.AscendingOrder)
        font = view.font()
        font.setPointSize(app.prefs.tableFontSize)
        view.setFont(font)
        fm = QFontMetrics(font)
        view.verticalHeader().setDefaultSectionSize(fm.height() + 2)
        app.willSavePrefs.connect(self.appWillSavePrefs)

    def _getData(self, row, column, role):
        if column.name == "marked":
            if role == Qt.CheckStateRole and row.markable:
                return Qt.Checked if row.marked else Qt.Unchecked
            return None
        if role == Qt.DisplayRole:
            return row.data[column.name]
        elif role == Qt.FontRole:
            return QFont(self.view.font())
        elif role == Qt.EditRole:
            if column.name == "regex":
                return row.data[column.name]
        return None

    def _getFlags(self, row, column):
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if column.name == "marked":
            if row.markable:
                flags |= Qt.ItemIsUserCheckable
        elif column.name == "regex":
            flags |= Qt.ItemIsEditable
        return flags

    def _setData(self, row, column, value, role):
        if role == Qt.CheckStateRole:
            if column.name == "marked":
                row.marked = bool(value)
                return True
        elif role == Qt.EditRole:
            if column.name == "regex":
                return self.model.rename_selected(value)
        return False

    def sort(self, column, order):
        column = self.model.COLUMNS[column]
        self.model.sort(column.name, order == Qt.AscendingOrder)

    # --- Events
    def appWillSavePrefs(self):
        self.model.columns.save_columns()

    # --- model --> view
    def invalidate_markings(self):
        # redraw view
        # HACK. this is the only way I found to update the widget without reseting everything
        self.view.scroll(0, 1)
        self.view.scroll(0, -1)


class ExcludeView(QTableView):
    def mouseDoubleClickEvent(self, event):
        # FIXME this doesn't seem to do anything relevant
        self.doubleClicked.emit(QModelIndex())
        # We don't call the superclass' method because the default behavior is to rename the cell.
