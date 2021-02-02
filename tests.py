import os
from time import sleep
import numpy as np
from PyQt5 import QtGui, QtWidgets

from plotWindow import dCursor, lineSeg
from script import calculArea, clipdn, clipup, clipx, delDupX, despike, fft
from script import line, linEq, lineFit, mergeb, name, ndec, newV, onset
from script import revertb, revertv, shift, shrink, sort, stats, swapv
from utils import textToData
from convIso import processBET, PSDcalc
from convCIF import CIF
from convert import convDAT, convPRF, convertShape, transpose, convert2D
from convert import convertToAbs, convertToTrans

# - testDlg class ------------------------------------------------------------

class testDlg(QtWidgets.QDialog):
    def __init__(self, parent=None, group=None):
        """ Test dialog.

        :param parent: pyDataVis MainWindow.
        :param group: class of the tests ("script", "IO", "Convert")
        """
        super(testDlg, self).__init__(parent)
        info = "Test information is shown in the Text editor Window\n\n"
        info += "Hit the space bar to pause the testing process.\n"
        info += "Hit the Esc key to cancel the testing process.\n\n"
        info += "Select the test"
        infolab = QtWidgets.QLabel(info)
        self.testComboBox = QtWidgets.QComboBox(self)
        self.testlist = ["All tests"]
        if group == "script":
            self.setWindowTitle('Tests of script commands')
            self.testlist.extend(sctstnam)
        if group == "IO":
            self.setWindowTitle('Tests of Input/Output')
            self.testlist.extend(iotstnam)
        if group == "Convert":
            self.setWindowTitle('Tests of convert options')
            self.testlist.extend(convtstnam)
        self.testComboBox.addItems(self.testlist)
        # Buttons
        okBtn = QtWidgets.QPushButton("OK")
        cancelBtn = QtWidgets.QPushButton("Cancel")
        # set the layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(infolab)
        vbox.addWidget(self.testComboBox)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(okBtn)
        hbox.addWidget(cancelBtn)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

        # Connect buttons to callback functions
        okBtn.clicked.connect(self.accept)
        cancelBtn.clicked.connect(self.reject)


def wait(tim, mainw):
    """ Wait for 'tim' seconds

    :param mainw: the application MainWindow
    :param tim: the number of seconds to wait.
    :return: False if the user has pressed the Esc key.
    """
    for i in range(tim*10):
       if mainw.keyb == "escape":
           mainw.keyb = None
           return False
       if mainw.keyb == " ":
           mainw.keyb = None
           msgBox = QtWidgets.QMessageBox()
           msgBox.setIcon(QtWidgets.QMessageBox.Information)
           msgBox.setText("Ok to resume or Cancel to cancel")
           msgBox.setWindowTitle("Testing process paused")
           msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
           if msgBox.exec() == QtWidgets.QMessageBox.Cancel:
               return False
       sleep(0.1)
       mainw.app.processEvents()
    return True


def runTests(mainw, sel):
    """ Run the self tests

    :param mainw:
    :return: Nothing
    """
    if sel == "Run script tests":
        group = "script"
        tstfunc = sctstfunc
        tstnam = sctstnam
        title = "Script Tests results"
    elif sel == "Run I/O tests":
        group = "IO"
        tstfunc = iotstfunc
        tstnam = iotstnam
        title = "Input/Output Tests results"
    elif sel == "Run convert tests":
        group = "Convert"
        tstfunc = convtstfunc
        tstnam = convtstnam
        title = "Convert Tests results"
    else:
        return
    dlg = testDlg(mainw, group)
    dlg.setModal(True)
    ret = dlg.exec_()
    if not ret:
        return

    mainw.keyb = None
    pos = dlg.testComboBox.currentIndex()
    if pos == 0:
        # run all tests
        result = []
        for i, func in enumerate(tstfunc):
            err, msg = func(mainw)
            if err == -1:
                # user interruption
                break
            if err == 0:
                res = "passed"
            else:
                res = "failed\n{0}".format(msg)
            result.append("{0} test {1}".format(tstnam[i], res))
        result = '\n'.join(result)
    else:
        err, msg = tstfunc[pos - 1](mainw, extratim=3)
        if err == -1:
            res = "stopped by user"
        elif err == 0:
            res = "passed"
        else:
            res = "failed\n{0}".format(msg)
        result = "{0} test : {1}".format(tstnam[pos - 1], res)
    if result:
        QtWidgets.QMessageBox.information(mainw, title, result)


# ------------------------------------------------------------------------

def test_area(mainw, extratim=0):
    """ Test the 'area' script command.

        This also test Cursor and Marker
    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "area.plt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    err = 0
    pltw = subw.widget()
    pltw.dcursor = dCursor(pltw)
    if pltw.dcursor.move(indx=566):
        info = "#### Test of the 'area' script command ####\n"
        info += "# Test file: /selftests/area.plt\n"
        info += "# Set Cursor at X = 250"
        pltw.datatext.setText(info)
        if not wait(2, mainw):
            err = -1
    else:
        err = 1
        msg = "Data cursor error"
    if not err:
        mainw.addMark()
        info += "\n# Set a marker at cursor position"
        pltw.datatext.setText(info)
        if not wait(2, mainw):
            err = -1
    if not err:
        if pltw.dcursor.move(indx=900):
            info += "\n# Set Cursor at X = 362"
            pltw.datatext.setText(info)
            if not wait(2, mainw):
                err = -1
        else:
            err = 1
            msg = "Data cursor error"
    if not err:
        mainw.addMark()
        info += "\n# Set a marker at cursor position"
        pltw.datatext.setText(info)
        if not wait(2, mainw):
            err = -1
    if not err:
        # Area between 250.792 and 362.125 = 5562.28
        result = calculArea(pltw, pltw.curvelist[0], 566, 900)
        if result:
            info = "#\n# {0}\n\nEnd of the test".format(result)
            pltw.datatext.setText(info)
            if not wait(3 + extratim, mainw):
                err = -1
        else:
            err = 1
            msg = "Calcul area error"
    subw.close()
    return err, msg


def test_BET(mainw, extratim=0):
    """ Test the 'BET' script command.

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "BET.plt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    err = 0
    pltw = subw.widget()
    info = "#### Test of the 'BET' script command ####\n"
    info += "# Test file: /selftests/BET.plt\n"
    pltw.datatext.setText(info)
    if not wait(2, mainw):
        err = -1
    else:
        (msg, bestprm, Pri, Prf) = processBET(pltw.blklst[0])
        if msg:
            err = 1
    if not err:
        info += "# Computing BET surface area\n"
        info += '# BET Surface Area : {0:7.2f} m2/g\n'.format(bestprm.SBET)
        info += '# Correlation Coefficient :  {0:4.5f} \n\n'.format(bestprm.cc)
        info += "# End of the test"
        pltw.datatext.setText(info)
        if not wait(2 + extratim, mainw):
            err = -1
    subw.close()
    return err, msg


def test_clipupdn(mainw, extratim=0):
    """ Test the 'clipup' and 'clipdn' script command.

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "clipupdn.plt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    err = 0
    pltw = subw.widget()
    info = "#### Test of the 'clipup' and 'clipdn' script command ####\n"
    info += "# Test file: /selftests/clipupdn.plt\n\n"
    info += "# First, testing 'clipup' script command \n"
    pltw.datatext.setText(msg)
    if not wait(4, mainw):
        err = -1
    else:
        err, msg = clipup(pltw, 'Y', 1.0)
        if not err:
            pltw.updatePlot()
            info += "# Using 'clipup Y 1' to clip Y > 1.0\n"
            pltw.datatext.setText(info)
            if not wait(3, mainw):
                err = -1
    if not err:
        info = "# Now, testing 'clipdn' script command \n\n"
        info += "# Using 'clipdn Y -1' to clip Y < -1.0\n\n"
        info += "# End of the test"
        err, msg = clipdn(pltw, 'Y', -1.0)
        if not err:
            pltw.updatePlot()
            pltw.datatext.setText(info)
            if not wait(3 + extratim, mainw):
                err = -1
    subw.close()
    return err, msg


def test_clipx(mainw, extratim=0):
    """ Test the 'clipx' script command.

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "clipx.plt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    err = 0
    pltw = subw.widget()
    info = "#### Test of the 'clipx' script command ####\n"
    info += "# Test file: /selftests/clipx.plt\n\n"
    pltw.datatext.setText(info)
    if not wait(3, mainw):
        err = -1
    else:
        err, msg = clipx(pltw, 30, '>')
        if not err:
            pltw.updatePlot()
            info += "# Using 'clipx > 30' to remove X values > 30\n"
            info += "\n# End of the test"
            pltw.datatext.setText(info)
            if not wait(2 + extratim, mainw):
                err = -1
    subw.close()
    return err, msg


def test_delb(mainw, extratim=0):
    """ Test the 'delb' script command.

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "delb.plt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    err = 0
    pltw = subw.widget()
    info = "#### Test of the 'delb' script command ####\n"
    info += "# Test file: /selftests/delb.plt\n\n"
    info += "# This file contains 3 data blocks.\n"
    info += "# We will delete the block no 2."
    pltw.datatext.setText(info)
    if not wait(3, mainw):
        err = -1
    else:
        info += "\n# Executing 'delb 2' command\n"
        info += "# End of the test"
        pltw.datatext.setText(info)
        if pltw.delBlock(1):
            pltw.dirty = False
            if not wait(3 + extratim, mainw):
                err = -1
        else:
            err = 1
            msg = "Wrong block number"
    subw.close()
    return err, msg


def test_deldupx(mainw, extratim=0):
    """ Test the 'deldupx' script command.

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "deldupx.plt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    pltw = subw.widget()
    info = "#### Test of the 'deldupx' script command ####\n"
    info += "# Test file: /selftests/deldupx.plt\n\n"
    pltw.datatext.setText(info)
    if not wait(3, mainw):
        err = -1
    else:
        err, msg = delDupX(pltw, 'X')
    if not err:
        info += "# {0}\n\n# End of the test".format(msg)
        pltw.datatext.setText(info)
        if not wait(2 + extratim, mainw):
            err = -1
    subw.close()
    return err, msg


def test_delv(mainw, extratim=0):
    """ Test the 'delv' script command.

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "delv.plt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    err = 0
    pltw = subw.widget()
    info = "#### Test of the 'delv' script command ####\n"
    info += "# Test file: /selftests/delv.plt\n\n"
    pltw.datatext.setText(info)
    if not wait(2, mainw):
        err = -1
    else:
        info += "# Execute 'delv Pd' command\n\n"
        info += "# End of the test"
        pltw.datatext.setText(info)
        if pltw.delVector('Pd'):
            pltw.dirty = False
            if not wait(2 + extratim, mainw):
                err = -1
        else:
            err = 1
            msg = "Error in vector name"
    subw.close()
    return err, msg


def test_despike(mainw, extratim=0):
    """ Test the 'despike' script commands.

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "despike.plt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    pltw = subw.widget()
    info = "#### Test of the 'despike' script command ####\n"
    info += "# Test file: /selftests/despike.plt\n\n"
    pltw.datatext.setText(info)
    if not wait(3, mainw):
        err = -1
    else:
        info += "# Execute 'despike I 3' command\n"
        info += "# End of the test"
        pltw.datatext.setText(info)
        err, msg = despike(pltw, 'I', 3)
    if not err:
        pltw.updatePlot()
        if not wait(3 + extratim, mainw):
            err = -1
    subw.close()
    return err, msg


def test_fft(mainw, extratim=0):
    """ Test the 'FFT' script command.

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "fft.plt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    pltw = subw.widget()
    info = "#### Test of the 'fft' script command ####\n"
    info += "# Test file: /selftests/fft.plt\n\n"
    pltw.datatext.setText(info)
    if not wait(1 + extratim, mainw):
        err = -1
    else:
        err, msg = fft(pltw, 'Y')
    if not err:
        info += "# Execute 'fft Y' command\n"
        info += "# This creates and loads the file Y-fft.txt\n\n"
        info += "# End of the test"
        pltw.datatext.setText(info)
        if not wait(3 + extratim, mainw):
            err = -1
        fftnam = "{0}/Y-fft.txt".format(mainw.progpath)
        subwfft = mainw.isAlreadyOpen(fftnam)
        if subwfft is not None:
            subwfft.close()
    subw.close()
    return err, msg


def test_IR(mainw, extratim=0):
    """ Test the 'IRtrans' and 'IRabs' script commands.

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "IR.plt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    pltw = subw.widget()
    info = "#### Test of the 'IRabs' and 'IRtrans' script commands ####\n"
    info += "# Test file: /selftests/IR.plt\n\n"
    pltw.datatext.setText(info)
    if not wait(2, mainw):
        err = -1
    else:
        info = "##### First testing 'IRabs' script command #####\n\n"
        pltw.datatext.setText(info)
        err, msg = convertToAbs(pltw.blklst[0])
    if not err:
        pltw.updatePlot()
        if not wait(2 + extratim, mainw):
            err = -1
    if not err:
        info = "##### Now testing 'IRtrans' script command #####\n\n"
        info += "# End of the test"
        pltw.datatext.setText(info)
        err, msg = convertToTrans(pltw.blklst[0])
        if not err:
            pltw.updatePlot()
            if not wait(3 + extratim, mainw):
                err = -1
    subw.close()
    return err, msg


def test_line(mainw, extratim=0):
    """ Test the 'line' script command.

        This also test Cursor and Marker
    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "line.plt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    err = 0
    pltw = subw.widget()
    info = "#### Test of the 'line' script commands ####\n"
    info += "# Test file: /selftests/line.plt\n"
    pltw.datatext.setText(info)
    if not wait(2, mainw):
        err = -1
    pltw.dcursor = dCursor(pltw)
    if pltw.dcursor.move(indx=270):
        info += "# Set Cursor at X = 28.5\n"
        pltw.datatext.setText(info)
        if not wait(2, mainw):
            err = -1
    else:
        err = 1
        msg = "Data cursor error"
    if not err:
        mainw.addMark()
        info += "# Set a marker at cursor position\n"
        pltw.datatext.setText(info)
        if not wait(2, mainw):
            err = -1
    if not err:
        if pltw.dcursor.move(indx=414):
            info += "# Set Cursor at X = 33.0\n"
            pltw.datatext.setText(info)
            if not wait(2, mainw):
                err = -1
        else:
            err = 1
            msg = "Data cursor error"
    if not err:
        mainw.addMark()
        info += "# Set a marker at cursor position\n"
        pltw.datatext.setText(info)
        if not wait(2, mainw):
            err = -1
    if not err:
        err, ms = line(pltw, 'Y')
        if not err:
            pltw.updatePlot()
            info += "# Executing 'line Y' clears the second peak\n\n"
            info += "# End of the test"
            pltw.datatext.setText(info)
            if not wait(3 + extratim, mainw):
                err = -1
    subw.close()
    return err, msg


def test_linefit(mainw, extratim=0):
    """ Test the 'linefit' script command.

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "linefit.plt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    err = 0
    pltw = subw.widget()
    info = "#### Test of the 'linefit' script commands ####\n"
    info += "# Test file: /selftests/linefit.plt\n"
    pltw.datatext.setText(info)
    if not wait(3, mainw):
        err = -1
    else:
        pltw.dcursor = dCursor(pltw)
        if pltw.dcursor.move(indx=53):
            info += "# Set Cursor on the left side of the peak"
            pltw.datatext.setText(info)
            if not wait(3, mainw):
                err = -1
        else:
            err = 1
            msg = "Data cursor error"
    if not err:
        err, msg = lineFit(pltw, pltw.curvelist[0], 53, 1)
        if not err:
            info = "# Execute 'linefit Y' "
            info += "\n{}\n".format(msg)
            info += "\n# End of the test"
            pltw.datatext.setText(msg)
            if not wait(3 + extratim, mainw):
                err = -1
    subw.close()
    return err, msg


def test_lineq(mainw, extratim=0):
    """ Test the 'lineq' script command.

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "lineq.plt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    err = 0
    pltw = subw.widget()
    info = "#### Test of the 'lineq' script commands ####\n"
    info += "# Test file: /selftests/lineq.plt\n"
    pltw.datatext.setText(info)
    if not wait(2 + extratim, mainw):
        err = -1
    else:
        pltw.dcursor = dCursor(pltw)
        if pltw.dcursor.move(indx=20):
            info += "# Set Cursor at X = 1.0\n"
            pltw.datatext.setText(info)
            if not wait(2, mainw):
                err = -1
        else:
            err = 1
            msg = "Data cursor error"
    if not err:
        mainw.addMark()
        info += "# Set a marker at cursor position\n"
        pltw.datatext.setText(info)
        if not wait(2, mainw):
            err = -1
    if not err:
        if pltw.dcursor.move(indx=60):
            info += "# Set Cursor at X = 3.0\n"
            pltw.datatext.setText(info)
            if not wait(2, mainw):
                err = -1
        else:
            err = 1
            msg = "Data cursor error"
    if not err:
        mainw.addMark()
        info += "# Set a marker at cursor position\n"
        pltw.datatext.setText(info)
        if not wait(2, mainw):
            err = -1
    if not err:
        err, msg = linEq(pltw, pltw.curvelist[0], 20, 60)
        x1 = pltw.blklst[0][0][20]
        y1 = pltw.blklst[0][1][20]
        x2 = pltw.blklst[0][0][60]
        y2 = pltw.blklst[0][1][60]
        pltw.lineList.append(lineSeg(x1, y1, x2, y2, 'red'))
        pltw.updatePlot()
        if not err:
            info = "# Execute 'lineq Y' \n"
            info += "{0}\n\n# End of the test".format(msg)
            pltw.datatext.setText(info)
            if not wait(3 + extratim, mainw):
                err = -1
    subw.close()
    return err, msg


def test_mergeb(mainw, extratim=0):
    """ Test the 'mergeb' script command.

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "mergeb.txt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    pltw = subw.widget()
    info = "#### Test of the 'mergeb' script commands ####\n"
    info += "# Test file: /selftests/mergeb.txt\n\n"
    info += "# This file contains two data blocks with only one vector, \n"
    info += "# The 'mergeb 1 2' command will merge these blocks such as \n"
    info += "# there will be only one data block containing 2 vectors \n"
    pltw.datatext.setText(info)
    if not wait(4, mainw):
        err = -1
    else:
        err, msg = mergeb(pltw, [1, 2])
    if not err:
        tmpnam = "{0}/selftests/tmp.txt".format(mainw.testspath)
        done = pltw.save(tmpnam)
        if done:
            pltw.load(tmpnam)
            info += "# Execute 'mergeb 1 2' \n"
            info += "# End of the test"
            pltw.datatext.setText(info)
            if not wait(4 + extratim, mainw):
                err = -1
    subw.close()
    return err, msg


def test_ndec(mainw, extratim=0):
    """ Test the 'ndec' script command.

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "ndec.plt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    pltw = subw.widget()
    mainw.tableTool()
    info = "#### Test of the 'ndec' script commands ####\n"
    info += "# Test file: /selftests/ndec.plt\n"
    info += "# Display the data table"
    pltw.datatext.setText(info)
    if not wait(5, mainw):
        err = -1
    else:
        err, msg = ndec(pltw, 'Y', 2)
        pltw.tabledlg.table.initTable()
    if not err:
        info += "\n# Execute 'ndec Y 2' command"
        info += "\n# Now, the Y values are rounded to 2 decimal place"
        info += "\n\n# End of the test"
        pltw.datatext.setText(info)
        if not wait(5 + extratim, mainw):
            err = -1
        pltw.tabledlg.close()
    subw.close()
    return err, msg


def test_newv(mainw, extratim=0):
    """ Test the 'newv' script command.

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    mainw.fileNew()
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    pltw = subw.widget()
    info = "#### Test of the 'newv' script commands ####\n"
    pltw.datatext.setText(info)
    if not wait(1, mainw):
        err = -1
    else:
        err, msg = newV(pltw, "newv X 0,10,0.1")
    if not err:
        info += "# Executing 'newv X 0,10,0.1' command\n"
        info += "# This create a new vector X and\n"
        info += "# a new data block for hosting X\n"
        info += "\n# End of the test"
        pltw.datatext.setText(info)
        pltw.displayInfo()
    if not wait(4 + extratim, mainw):
        err = -1
    pltw.dirty = False
    subw.close()
    return err, msg


def test_onset(mainw, extratim=0):
    """ Test the 'linefit' script command.

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "onset.plt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    pltw = subw.widget()
    info = "#### Test of the 'onset' script commands ####\n"
    info += "# Test file: /selftests/onset.plt\n"
    pltw.datatext.setText(info)
    if not wait(2, mainw):
        err = -1
    else:
        err = 0
        pltw.dcursor = dCursor(pltw)
        if pltw.dcursor.move(indx=45):
            info += "# Set Cursor on the baseline\n"
            pltw.datatext.setText(info)
            if not wait(2, mainw):
                err = -1
        else:
            err = 1
            msg = "Data cursor error"
    if not err:
        mainw.addMark()
        info += "# Set a marker at cursor position\n"
        pltw.datatext.setText(info)
        if not wait(2, mainw):
            err = -1
    if not err:
        if pltw.dcursor.move(indx=52):
            info += "# Set Cursor on the left side of the peak\n"
            pltw.datatext.setText(info)
            if not wait(2, mainw):
                err = -1
        else:
            err = 1
            msg = "Data cursor error"
    if not err:
        mainw.addMark()
        info += "# Set a marker at cursor position\n"
        pltw.datatext.setText(info)
        if not wait(2, mainw):
            err = -1
    if not err:
        err, msg = onset(pltw, pltw.curvelist[0], 45, 52)
        if not err:
            info += "# Execute 'onset Y' command"
            info += "{0}\n# End of the test".format(msg)
            pltw.datatext.setText(info)
            if not wait(5 + extratim, mainw):
                err = -1
    subw.close()
    return err, msg


def test_PSD(mainw, extratim=0):
    """ Test the 'PSD' script command.

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    if mainw.progpath is None:
        # Because it will be impossible to create the temporary file
        return 1, "Cannot create the temporary file"
    path = os.path.join(mainw.testspath, "selftests", "PSD-iso.plt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    pltw = subw.widget()
    info = "#### Test of the 'PSD' script commands ####\n"
    info += "# Test file: /selftests/PSD-iso.plt\n"
    pltw.datatext.setText(info)
    if not wait(3, mainw):
         err = -1
    else:
         psdnam = "{0}/PSD-PSD.plt".format(mainw.progpath)
         err, msg = PSDcalc(pltw.blklst[1], psdnam, 'D', "halsey")
    if not err:
        info += "\n# Execute 'PSD D halsey' command"
        pltw.datatext.setText(info)
        if not wait(2, mainw):
            err = -1
    if not err:
        msg = mainw.loadFile(psdnam)
        if msg == "":
            if not wait(4+extratim, mainw):
                err = -1
            subwpsd = mainw.isAlreadyOpen(psdnam)
            if subwpsd is not None:
                subwpsd.close()
        else:
            err = 1
    subw.close()
    return err, msg


def test_revert(mainw, extratim=0):
    """ Test the 'revert' script command.

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "revert.plt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    pltw = subw.widget()
    mainw.tableTool()
    info = "#### Test of the 'revertv and 'revertb' script commands ####\n"
    info += "# Test file: /selftests/revert.plt\n"
    info += "# Display the data table"
    pltw.datatext.setText(info)
    if not wait(3, mainw):
        err = -1
    else:
        err, msg = revertv(pltw, 'X')
    if not err:
        pltw.updatePlot()
        pltw.tabledlg.table.initTable()
        info += "\n# After executing 'revertv X' command"
        info += "\n# The data in X are now in reverse order"
        pltw.datatext.setText(info)
        if not wait(3, mainw):
            err = -1
    if not err:
        err, msg = revertb(pltw, 0)
    if not err:
        pltw.updatePlot()
        pltw.tabledlg.table.initTable()
        info += "\n\n# After executing 'revertb 1' command"
        info += "\n# The data in X and Y are now in reverse order"
        info += "\n\n# End of the test"
        pltw.datatext.setText(info)
        if not wait(3 + extratim, mainw):
            err = -1
        pltw.tabledlg.close()
    subw.close()
    return err, msg


def test_shift(mainw, extratim=0):
    """ Test the 'shift' script command.

        This also test Cursor and Marker
    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "shift.plt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    pltw = subw.widget()
    info = "#### Test of the 'shift' script commands ####\n"
    info += "# Test file: /selftests/shift.plt\n"
    pltw.datatext.setText(info)
    if not wait(3, mainw):
        err = -1
    else:
        err = 0
    pltw.dcursor = dCursor(pltw)
    if pltw.dcursor.move(indx=20):
        info += "# Set Cursor at X = 2\n"
        pltw.datatext.setText(info)
        if not wait(2, mainw):
            err = -1
    else:
        err = 1
        msg = "Data cursor error"
    if not err:
        mainw.addMark()
        info += "# Set a marker at cursor position\n"
        pltw.datatext.setText(info)
        if not wait(2, mainw):
            err = -1
    if not err:
        if pltw.dcursor.move(indx=60):
            info += "# Set Cursor at X = 6\n"
            pltw.datatext.setText(info)
            if not wait(2, mainw):
                err = -1
        else:
            err = 1
            msg = "Data cursor error"
    if not err:
        mainw.addMark()
        info += "# Set a marker at cursor position\n"
        pltw.datatext.setText(info)
        if not wait(2, mainw):
            err = -1
    if not err:
        err, msg = shift(pltw, pltw.curvelist[0], -0.6, 20, 60)
        if not err:
            pltw.updatePlot()
            info += "# Execute 'shift Y -0.6' command"
            info += "\n# End of the test"
            pltw.datatext.setText(info)
            if not wait(3 + extratim, mainw):
                err = -1
    subw.close()
    return err, msg


def test_shrink(mainw, extratim=0):
    """ Test the 'shrink' script command.

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "shrink.plt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    pltw = subw.widget()
    info = "#### Test of the 'shrink' script commands ####\n"
    info += "# Test file: /selftests/shrink.plt\n"
    pltw.datatext.setText(info)
    if not wait(3, mainw):
        err = -1
    else:
        info += "# Execute the command 'shrink TG 5'\n"
        err, msg = shrink(pltw, 'TG', 5)
    if not err:
        info += "\n# {0}\n\n# End of the test".format(msg)
        pltw.datatext.setText(info)
        if not wait(4 + extratim, mainw):
            err = -1
    subw.close()
    return err, msg


def test_sort(mainw, extratim=0):
    """ Test the 'sort' script command.

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "sort.plt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    pltw = subw.widget()
    info = "#### Test of the 'sort' script commands ####\n"
    info += "# Test file: /selftests/sort.plt\n"
    info += "# This is the curve of Y = X*X but X values are not sorted."
    pltw.datatext.setText(info)
    if not wait(4, mainw):
        err = -1
    else:
        err, msg = sort(pltw, 'X')
    if not err:
        pltw.updatePlot()
        info += "\n# After executing 'sort X' command"
        info += "\n\n# End of the test"
        pltw.datatext.setText(info)
        if not wait(4 + extratim, mainw):
            err = -1
    subw.close()
    return err, msg


def test_stats(mainw, extratim=0):
    """ Test the 'stats' script command.

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "stats.plt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    pltw = subw.widget()
    info = "#### Test of the 'stats' script commands ####\n"
    info += "# Test file: /selftests/stats.plt\n"
    info += "# About to execute 'stats Y' command"
    pltw.datatext.setText(info)
    if not wait(3, mainw):
        err = -1
    else:
        err, msg = stats(pltw, 'Y')
    if not err:
        pltw.datatext.setText(msg)
        if not wait(5 + extratim, mainw):
            err = -1
    subw.close()
    return err, msg


def test_swapv(mainw, extratim=0):
    """ Test the 'swapv' script command.

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "swapv.plt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    pltw = subw.widget()
    info = "#### Test of the 'swapv' script commands ####\n"
    info += "# Test file: /selftests/swapv.plt"
    pltw.datatext.setText(info)
    if not wait(3, mainw):
        err = -1
    else:
        err, ms = swapv(pltw, 'X', 'Y')
    if not err:
        pltw.updatePlot()
        info += "\n# After executing 'swapv X Y' command"
        info += "\n\n# End of the test"
        pltw.datatext.setText(info)
        if not wait(3 + extratim, mainw):
            err = -1
        subw.close()
    return err, msg


# ------------------------------------------------------------------------

sctstnam = ["area", "BET", "clipup & clipdn", "clipx", "delb", "deldupx",
            "delv", "despike", "fft", "IR", "line", "linefit", "lineq",
            "mergeb", "ndec", "newv", "onset", "PSD", "revert", "shift",
            "shrink", "sort", "stats", "swapv"]

sctstfunc = [test_area, test_BET, test_clipupdn, test_clipx, test_delb,
            test_deldupx, test_delv, test_despike, test_fft, test_IR,
            test_line, test_linefit, test_lineq, test_mergeb, test_ndec,
            test_newv, test_onset, test_PSD, test_revert, test_shift,
            test_shrink, test_sort, test_stats, test_swapv ]

# ------------------------------------------------------------------------

def test_sep(mainw, extratim=0):
    """ Test reading files with various separators

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    seplst = ["colon", "comma", "semicolon", "space", "tab"]
    info = "#### Testing various column separators #### \n\n"
    err = 0
    for sep in seplst:
        if sep == "comma":
            ext = "csv"
        else:
            ext = "txt"

        filnam = "sep-{0}.{1}".format(sep, ext)
        path = os.path.join(mainw.testspath, "selftests", filnam)
        msg = mainw.loadFile(path)
        if msg:
            err = 1
        else:
            subw = mainw.getCurrentSubWindow()
            if subw is None:
                return 1, "QtGui.QMdiArea error"
            pltw = subw.widget()
            info += "Reading a file where column separator is {0}\n".format(sep)
            info += "# Test file: /selftests/sep-{0}.txt\n\n".format(sep)
            if sep == "tab":
                info += "# End of the test"
            pltw.datatext.setText(info)
            pltw.datatext.moveCursor(QtGui.QTextCursor.End)
            if not wait(4, mainw):
                err = -1
            subw.close()
        if err:
            break
    return err, msg


def test_JCAMP(mainw, extratim=0):
    """ Test reading JCAMP-DX files

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    err = 0
    chemlst = ["1-Propanol-IR", "EtOH-IR", "acetone-MS", "AcetylAcetone-MS",
               "Ethanol-NMR"]
    for i, chem in enumerate(chemlst):
        filnam = "{0}.jdx".format(chem)
        path = os.path.join(mainw.testspath, "selftests", filnam)
        msg = mainw.loadFile(path)
        if msg != "":
            err = 1
        else:
            subw = mainw.getCurrentSubWindow()
            if subw is None:
                msg = "QtGui.QMdiArea error"
            else:
                pltw = subw.widget()
                info = "#### Reading a JCAMP-DX file ####\n"
                info += "# Test file: /selftests/{0}.jdx\n\n".format(chem)
                if i == len(chemlst) - 1:
                    info += "\n# End of the test"
                pltw.datatext.setText(info)
                if not wait(4, mainw):
                    err = -1
                subw.close()
            if err:
                break
    return err, msg


def test_RRUFF(mainw, extratim=0):
    """ Test reading RRUFF files

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    err = 0
    chemlst = ["TiO2-Anatase-Raman", "TiO2-Rutile-Raman"]
    for i, chem in enumerate(chemlst):
        filnam = "{0}.txt".format(chem)
        path = os.path.join(mainw.testspath, "selftests", filnam)
        msg = mainw.loadFile(path)
        if msg != "":
            err = 1
        else:
            subw = mainw.getCurrentSubWindow()
            if subw is None:
                msg = "QtGui.QMdiArea error"
            else:
                pltw = subw.widget()
                info = "#### Reading a RRUFF Raman file ####\n"
                info += "# Test file: /selftests/{0}.txt\n\n".format(chem)
                if i == len(chemlst) - 1:
                    info += "\n# End of the test"
                pltw.datatext.setText(info)
                if not wait(4, mainw):
                    err = -1
                subw.close()
            if err:
                break
    return err, msg


def test_append(mainw, extratim=0):
    """ Test the Append option in file menu

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "append-1.plt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    err = 0
    pltw = subw.widget()
    info = "#### Testing Append option in file menu ####\n"
    info += "# Test file: /selftests/append-1.plt\n\n"
    pltw.datatext.setText(info)
    if not wait(3, mainw):
        err = -1
    if not err:
        path = os.path.join(mainw.testspath, "selftests", "append-2.plt")
        msg = mainw.appendFile(path)
        if msg is not None:
            err = 1
        else:
            info += "# The file data in: /selftests/append-2.plt\n"
            info += "# has been added at the end of the initial data\n"
            info += "\n# End of the test"
            pltw.datatext.setText(info)
            if not wait(3, mainw):
                err = -1
    pltw.dirty = False
    subw.close()
    return err, msg


def test_export_csv(mainw, extratim=0):
    """ Test the 'Export to CSV' option in file menu

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "ExportToCSV.plt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    err = 1
    pltw = subw.widget()
    info = "#### Testing 'Export to CSV' option in file menu ####\n"
    info += "# Test file: /selftests/ExportToCSV.plt\n\n"
    path = "{0}/selftests/exported.csv".format(mainw.testspath)
    if pltw.exportToCSV(0, path):
        info += "The data block has been exported in 'exported.csv'"
        # Read the exported file to check it is ok.
        msg, ftext = pltw.fileToString(path)
        if ftext is not None:
            txtlines = ftext.splitlines()
            msg, blocks, headers = textToData(txtlines, ',')
            if msg == "":
                err = 0
                info += "\n# End of the test"
                pltw.datatext.setText(info)
                if not wait(4, mainw):
                    err = -1
    subw.close()
    return err, msg


def test_export_xls(mainw, extratim=0):
    """ Test the 'Export to Excel' option in file menu

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "2-Block.plt")
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    pltw = subw.widget()
    info = "#### Testing 'Export to Excel' option in file menu ####\n"
    info += "# Test file: /selftests/2-Block.plt\n\n"
    path = "{0}/selftests/2-Sheet.xls".format(mainw.testspath)
    err, msg = mainw.exportExcel(pltw, path)
    if not err:
        info += "Two data blocks have been exported in '2-Sheet.xls'"
        info += "\n# End of the test"
        pltw.datatext.setText(info)
        if not wait(4, mainw):
            err = -1
    subw.close()
    return err, msg


def test_import(mainw, extratim=0):
    """ Test the 'Import from spreadsheet' option in file menu

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", "2-Sheet.xls")
    err, msg = mainw.importxls(path)
    if err:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    pltw = subw.widget()
    info = "#### Testing 'Import from spreadsheet' option in file menu ####\n"
    info += "# 1 - Import from Excel file \n"
    info += "# Test file: /selftests/2-Sheet.xls\n\n"
    if len(pltw.blklst) == 2:
        info += "Two sheets have been imported as two data blocks\n"
        pltw.datatext.setText(info)
        if not wait(4, mainw):
            err = -1
    else:
        err = 1
        msg = "Unexpected data size"
    subw.close()
    if err:
        return err, msg

    path = os.path.join(mainw.testspath, "selftests", "1-Sheet.ods")
    err, msg = mainw.importxls(path)
    if err:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    pltw = subw.widget()
    info = "# 2 - Import from Open Document file (ODF)\n"
    info += "# Test file: /selftests/1-Sheet.ods\n\n"
    if len(pltw.blklst) == 1:
        info += "One sheet has been imported in one data block\n"
        info += "\n# End of the test"
        pltw.datatext.setText(info)
        if not wait(4, mainw):
            err = -1
    else:
        err = 1
        msg = "Unexpected data size"
    subw.close()
    return err, msg


# ------------------------------------------------------------------------

iotstnam = ["test_sep", "test_JCAMP", "test_RRUFF", "test_append",
            "test_export_csv", "test_export_xls", "test_import"]

iotstfunc = [test_sep, test_JCAMP, test_RRUFF, test_append,
             test_export_csv, test_export_xls, test_import]


def convert(mainw, filnam, info, convfunc):
    """ Generic function for testing convert options in convert menu.

    :param mainw: the application MainWindow
    :param filnam: string with the name of the test file
    :param info: string with the informative text to show
    :param convfunc: the conversion function to call
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    path = os.path.join(mainw.testspath, "selftests", filnam)
    msg = mainw.loadFile(path)
    if msg:
        return 1, msg
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1, "QtGui.QMdiArea error"
    pltw = subw.widget()
    text = str(pltw.datatext.toPlainText()).rstrip('\r\n')
    lines = text.split('\n')
    err = 1
    pltw.datatext.setText(info)
    if not wait(2, mainw):
        err = -1
    # remove the file extension
    basename = os.path.splitext(path)[0]
    # the saved file name is obtained by replacement of the extension by .plt
    savename = "{0}.plt".format(basename)
    infnam = os.path.split(path)[1]
    outfnam = os.path.split(savename)[1]
    if convfunc == convertShape:
        msg = convfunc(lines, 2, savename)
    elif convfunc == transpose:
        msg = convfunc(mainw, savename)
    else:
        msg = convfunc(lines, savename)
    subw.close()
    if msg is None:
        # load the converted file
        msg = mainw.loadFile(savename)
        if not msg:
            subw = mainw.isAlreadyOpen(savename)
            if subw is not None:
                err = 0
                info += '{0} has been successfully used to generate {1}\n'.format(infnam, outfnam)
                info += "\n# End of the test"
                pltw = subw.widget()
                pltw.datatext.setText(info)
                if not wait(5, mainw):
                    err = -1
                subw.close()
    return err, msg

# ------------------------------------------------------------------------

def test_CIF(mainw, extratim=0):
    """ Test the 'CIF' option in convert menu

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    filnam = "Si-COD-9008566.cif"
    info = "#### Testing 'CIF' option in convert menu ####\n"
    info += "# This generates a diffraction pattern from a CIF file\n"
    info += "# Loading test file: /selftests/{0}\n\n".format(filnam)
    return convert(mainw, filnam, info, CIF)


def test_DAT(mainw, extratim=0):
    """ Test the 'DAT' option in convert menu

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    filnam = "urea.dat"
    info = "#### Testing 'DAT' option in convert menu ####\n"
    info += "# This converts a '.DAT' diffraction file in a tabular text\n"
    info += "# Loading test file: /selftests/{0}\n\n".format(filnam)
    return convert(mainw, filnam, info, convDAT)


def test_PRF(mainw, extratim=0):
    """ Test the 'PRF' option in convert menu

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    filnam = "Anatase.prf"
    info = "#### Testing 'PRF' option in convert menu ####\n"
    info += "# This converts a FullProf “.PRF” file in a tabular text\n"
    info += "# Loading test file: /selftests/{0}\n\n".format(filnam)
    return convert(mainw, filnam, info, convPRF)


def test_reshape(mainw, extratim=0):
    """ Test the 'Reshape' option in convert menu

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    filnam = "Reshape.txt"
    info = "#### Testing 'Reshape' option in convert menu ####\n"
    info += "# This changes the shape of a data block\n"
    info += "# Loading test file: /selftests/{0}\n\n".format(filnam)
    return convert(mainw, filnam, info, convertShape)


def test_transpose(mainw, extratim=0):
    """ Test the 'Transpose' option in convert menu

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    filnam = "Transpose.txt"
    info = "#### Testing 'Transpose' option in convert menu ####\n"
    info += "# This switches the rows and columns\n"
    info += "# Loading test file: /selftests/{0}\n\n".format(filnam)
    return convert(mainw, filnam, info, transpose)


def test_1Dto2D(mainw, extratim=0):
    """ Test the '1D->2D' option in convert menu

    :param mainw: the application MainWindow
    :return: a tuple (err, msg).
             err = 0 if success, 1 if failure and -1 if interrupted by user.
             msg = contains an error message ("" if not error)
    """
    filnam = "1D.txt"
    info = "#### Testing '1D->2D' option in convert menu ####\n"
    info += "# This adds a X column to a 1D data file\n"
    info += "# Loading test file: /selftests/{0}\n\n".format(filnam)
    return convert(mainw, filnam, info, convert2D)


# ------------------------------------------------------------------------

convtstnam = ["test_CIF", "test_DAT", "test_PRF", "test_reshape",
              "test_transpose", "test_1D->2D"]

convtstfunc = [test_CIF, test_DAT, test_PRF, test_reshape,
              test_transpose, test_1Dto2D]

