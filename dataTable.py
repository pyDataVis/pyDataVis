""" This module contains the dataTable class
"""
from PyQt5.QtCore import Qt, QFileInfo
from PyQt5 import QtGui, QtWidgets

import numpy as np

from utils import isNumber

# - dataTable class ------------------------------------------------------------

class dataTable(QtWidgets.QTableWidget):
    def __init__(self, pltw, parent=None):
        """ Data table is an instance of QTableWidget.

         :param parent: pyDataVis MainWindow.
         :param pltw: the active plotWin.
         """
        super(QtWidgets.QTableWidget, self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.pltw = pltw
        #self.resize(600, 600)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.cellClicked.connect(self.slotItemClicked)
        self.itemChanged.connect(self.slotItemChanged)


    def getCellValue(self, row, col):
        return str(self.data[col][row])


    def slotItemClicked(self, row, col):
        """ Callback function when the user click in the table cell.

        :param row:
        :param col:
        :return: nothing
        """
        self.currentRow = row
        if self.pltw.dcursor is not None:
            self.pltw.dcursor.setIndex(row)


    def slotItemChanged(self, item):
        """ Callback function when the user changes a cell content.

        :param row:
        :param col:
        :return: nothing
        """
        if not self.init:
            text = item.text()
            if isNumber(text):
                oldval = self.data[item.column()][item.row()]
                newval = float(text)
                if newval != oldval:
                    self.data[item.column()][item.row()] = newval
                    self.pltw.dirty = True
                    self.pltw.updatePlot()
                    if self.pltw.dcursor is not None:
                        self.pltw.dcursor.updateLinePos()


    def initTable(self):
        """ Initialize the table with the vectors of the data block.

        :return: nothing
        """
        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
        self.init = True
        cpos = self.pltw.activcurv
        self.blkno = self.pltw.curvelist[cpos].yvinfo.blkpos
        self.xpos = self.pltw.curvelist[cpos].xvinfo.vidx
        self.ypos = self.pltw.curvelist[cpos].yvinfo.vidx
        self.data = self.pltw.blklst[self.blkno]
        (nvec, nrow) = np.shape(self.data)
        self.nrows = nrow
        self.setRowCount(self.nrows)
        self.setColumnCount(nvec)
        vnamlist = []
        for i in range(len(self.pltw.vectInfolst[self.blkno])):
            vnamlist.append(self.pltw.vectInfolst[self.blkno][i].name)
        self.setHorizontalHeaderLabels(vnamlist)
        for row in range(self.nrows):
            for col in range(nvec):
                newitem = QtWidgets.QTableWidgetItem(self.getCellValue(row, col))
                self.setItem(row, col, newitem)

        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        # Set as current item the item at dcursor position
        if self.pltw.dcursor is not None:
            self.setCurrentPos(self.pltw.dcursor.getIndex())
        else:
            self.setCurrentPos(0)
        self.show()
        self.init = False
        QtWidgets.QApplication.restoreOverrideCursor()


    def setCurrentPos(self, pos):
        # Set as current item the item at cursor position
        if self.pltw.dcursor is not None:
            self.currentRow = pos
            item = self.item(self.currentRow, self.ypos)
            self.setCurrentItem(item)
            self.scrollToItem(item)


# tableDlg --------------------------------------------------------------

class tableDlg(QtWidgets.QDialog):
    def __init__(self, parent):
        super (tableDlg, self).__init__(parent)

        self.pltw = parent
        self.table = dataTable(self.pltw, self)

        # set the layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.table)
        self.setLayout(vbox)
        self.table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.setWindowTitle(QFileInfo(self.pltw.filename).fileName())
        self.table.initTable()


    def closeEvent(self, event):
        self.pltw.tabledlg = None
