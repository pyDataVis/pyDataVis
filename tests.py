from time import sleep
from PyQt5 import QtWidgets

from plotWindow import dCursor, lineSeg
from script import calculArea, clipdn, clipup, clipx, delDupX, despike, fft
from script import line, linEq, lineFit, mergeb, name, ndec, newV, onset
from script import revert, shift, shrink, sort, stats, swapv
from convIso import processBET, PSDcalc
from convert import convertToAbs, convertToTrans

# - testDlg class ------------------------------------------------------------

class testDlg(QtWidgets.QDialog):
    def __init__(self, parent=None):
        """ Test dialog.

        :param parent: pyDataVis MainWindow.
        """
        super(testDlg, self).__init__(parent)
        info = "Test information is shown in the Text editor Window\n\n"
        info += "Hit the space bar to pause the testing process.\n"
        info += "Hit the Esc key to cancel the testing process.\n\n"
        info += "Select the test"
        infolab = QtWidgets.QLabel(info)
        self.testComboBox = QtWidgets.QComboBox(self)
        self.testlist = ["All tests"]
        self.testlist.extend(tstnam)
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
        self.setWindowTitle('Tests')

# ------------------------------------------------------------------------

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



def test_area(mainw, extratim=0):
    """ Test the 'area' script command.

        This also test Cursor and Marker
    :param mainw: the application MainWindow
    :return: 0 if success, 1 if failure and -1 if interrupted by user.
    """
    err = 1
    if mainw.loadFile("{0}/selftests/area.plt".format(mainw.testspath)):
        subw = mainw.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            pltw.dcursor = dCursor(pltw)
            if pltw.dcursor.move(indx=566):
                msg = "#### Test of the 'area' script command ####\n"
                msg += "# Test file : /selftests/area.plt\n"
                msg += "# Set Cursor at X = 250"
                pltw.datatext.setText(msg)
                if not wait(3, mainw):
                    err = -1
                else:
                    err = 0
            else:
                err = 1
            if not err:
                mainw.addMark()
                msg += "\n# Set a marker at cursor position"
                pltw.datatext.setText(msg)
                if not wait(3, mainw):
                    err = -1
            if not err:
                if pltw.dcursor.move(indx=900):
                    msg += "\n# Set Cursor at X = 362"
                    pltw.datatext.setText(msg)
                    if not wait(3, mainw):
                        err = -1
                else:
                    err = 1
            if not err:
               mainw.addMark()
               msg += "\n# Set a marker at cursor position"
               pltw.datatext.setText(msg)
               if not wait(3, mainw):
                    err = -1
            if not err:
               # Area between 250.792 and 362.125 = 5562.28
               result = calculArea(pltw, pltw.curvelist[0], 566, 900)
               if result:
                   msg = "#\n# {0}\n\nEnd of the test".format(result)
                   pltw.datatext.setText(msg)
                   if not wait(4+extratim, mainw):
                       err = -1
               else:
                   err = 1
            subw.close()
    return err


def test_BET(mainw, extratim=0):
    """ Test the 'BET' script command.

    :param mainw: the application MainWindow
    :return: 0 if success, 1 if failure and -1 if interrupted by user.
    """
    err = 1
    if mainw.loadFile("{0}/selftests/BET.plt".format(mainw.testspath)):
        subw = mainw.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            msg = "#### Test of the 'BET' script command ####\n"
            msg += "# Test file : /selftests/BET.plt\n"
            pltw.datatext.setText(msg)
            if not wait(2, mainw):
                err = -1
            else:
                err = 0
                (errmsg, bestprm, Pri, Prf) = processBET(pltw.blklst[0])
                if errmsg:
                    err = 1
            if not err:
                msg += "# Computing BET surface area\n"
                msg += '# BET Surface Area : {0:7.2f} m2/g\n'.format(bestprm.SBET)
                msg += '# Correlation Coefficient :  {0:4.5f} \n\n'.format(bestprm.cc)
                msg += "# End of the test"
                pltw.datatext.setText(msg)
                if not wait(2+extratim, mainw):
                    err = -1
            subw.close()
    return err


def test_clipupdn(mainw, extratim=0):
    """ Test the 'clipup' and 'clipdn' script command.

    :param mainw: the application MainWindow
    :return: 0 if success, 1 if failure and -1 if interrupted by user.
    """
    err = 1
    if mainw.loadFile("{0}/selftests/clipupdn.plt".format(mainw.testspath)):
        subw = mainw.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            msg = "#### Test of the 'clipup' and 'clipdn' script command ####\n"
            msg += "# Test file : /selftests/clipupdn.plt\n\n"
            msg += "# First, testing 'clipup' script command \n"
            pltw.datatext.setText(msg)
            if not wait(4, mainw):
                err = -1
            else:
                err, ms = clipup(pltw, 'Y', 1.0)
                if not err:
                    pltw.updatePlot()
                    msg += "# Using 'clipup Y 1' to clip Y > 1.0\n"
                    pltw.datatext.setText(msg)
                    if not wait(3, mainw):
                        err = -1
            if not err:
                msg = "# Now, testing 'clipdn' script command \n\n"
                msg += "# Using 'clipdn Y -1' to clip Y < -1.0\n\n"
                msg += "# End of the test"
                err, ms = clipdn(pltw, 'Y', -1.0)
                if not err:
                    pltw.updatePlot()
                    pltw.datatext.setText(msg)
                    if not wait(3+extratim, mainw):
                        err = -1
            subw.close()
    return err


def test_clipx(mainw, extratim=0):
    """ Test the 'clipx' script command.

    :param mainw: the application MainWindow
    :return: 0 if success, 1 if failure and -1 if interrupted by user.
    """
    err = 1
    if mainw.loadFile("{0}/selftests/clipx.plt".format(mainw.testspath)):
        subw = mainw.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            msg = "#### Test of the 'clipx' script command ####\n"
            msg += "# Test file : /selftests/clipx.plt\n\n"
            pltw.datatext.setText(msg)
            if not wait(3, mainw):
                err = -1
            else:
                err, ms = clipx(pltw, 30, '>')
                if not err:
                    pltw.updatePlot()
                    msg += "# Using 'clipx > 30' to remove X values > 30\n"
                    msg += "\n# End of the test"
                    pltw.datatext.setText(msg)
                    if not wait(2+extratim, mainw):
                        err = -1
            subw.close()
    return err


def test_delb(mainw, extratim=0):
    """ Test the 'delb' script command.

    :param mainw: the application MainWindow
    :return: 0 if success, 1 if failure and -1 if interrupted by user.
    """
    err = 1
    if mainw.loadFile("{0}/selftests/delb.plt".format(mainw.testspath)):
        subw = mainw.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            msg = "#### Test of the 'delb' script command ####\n"
            msg += "# Test file : /selftests/delb.plt\n\n"
            msg += "# This file contains 3 data blocks.\n"
            msg += "# We will delete the block no 2."
            pltw.datatext.setText(msg)
            if not wait(3, mainw):
                err = -1
            else:
                msg += "\n# Executing 'delb 2' command\n"
                msg += "# End of the test"
                pltw.datatext.setText(msg)
                if pltw.delBlock(1):
                    err = 0
                    pltw.dirty = False
                    if not wait(3 + extratim, mainw):
                        err = -1
                else:
                    err = 1
            subw.close()
    return err


def test_deldupx(mainw, extratim=0):
    """ Test the 'deldupx' script command.

    :param mainw: the application MainWindow
    :return: 0 if success, 1 if failure and -1 if interrupted by user.
    """
    err = 1
    if mainw.loadFile("{0}/selftests/deldupx.plt".format(mainw.testspath)):
        subw = mainw.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            msg = "#### Test of the 'deldupx' script command ####\n"
            msg += "# Test file : /selftests/deldupx.plt\n\n"
            pltw.datatext.setText(msg)
            if not wait(3, mainw):
                err = -1
            else:
                err, ms = delDupX(pltw, 'X')
            if not err:
                msg += "# {0}\n\n# End of the test".format(ms)
                pltw.datatext.setText(msg)
                if not wait(2+extratim, mainw):
                    err = -1
                subw.close()
    return err


def test_delv(mainw, extratim=0):
    """ Test the 'delv' script command.

    :param mainw: the application MainWindow
    :return: 0 if success, 1 if failure and -1 if interrupted by user.
    """
    err = 1
    if mainw.loadFile("{0}/selftests/delv.plt".format(mainw.testspath)):
        subw = mainw.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            msg = "#### Test of the 'delv' script command ####\n"
            msg += "# Test file : /selftests/delv.plt\n\n"
            pltw.datatext.setText(msg)
            if not wait(2, mainw):
                err = -1
            else:
                msg += "# Execute 'delv Pd' command\n\n"
                msg += "# End of the test"
                pltw.datatext.setText(msg)
                if pltw.delVector('Pd'):
                    err = 0
                    pltw.dirty = False
                    if not wait(2 + extratim, mainw):
                        err = -1
                else:
                    err = 1
            subw.close()
    return err


def test_despike(mainw, extratim=0):
    """ Test the 'despike' script commands.

    :param mainw: the application MainWindow
    :return: 0 if success, 1 if failure and -1 if interrupted by user.
    """
    err = 1
    if mainw.loadFile("{0}/selftests/despike.plt".format(mainw.testspath)):
        subw = mainw.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            msg = "#### Test of the 'despike' script command ####\n"
            msg += "# Test file : /selftests/despike.plt\n\n"
            pltw.datatext.setText(msg)
            if not wait(3, mainw):
                err = -1
            else:
                msg += "# Execute 'despike I 3' command\n"
                msg += "# End of the test"
                pltw.datatext.setText(msg)
                err, ms = despike(pltw, 'I', 3)
            if not err:
                pltw.updatePlot()
                if not wait(3+extratim, mainw):
                    err = -1
            subw.close()
    return err



def test_fft(mainw, extratim=0):
    """ Test the 'FFT' script command.

    :param mainw: the application MainWindow
    :return: 0 if success, 1 if failure and -1 if interrupted by user.
    """
    err = 1
    if mainw.loadFile("{0}/selftests/fft.plt".format(mainw.testspath)):
        subw = mainw.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            msg = "#### Test of the 'fft' script command ####\n"
            msg += "# Test file : /selftests/fft.plt\n\n"
            pltw.datatext.setText(msg)
            if not wait(1+extratim, mainw):
                err = -1
            else:
                err, ms = fft(pltw, 'Y')
            if not err:
                msg += "# Execute 'fft Y' command\n"
                msg += "# This creates and loads the file Y-fft.txt\n\n"
                msg += "# End of the test"
                pltw.datatext.setText(msg)
                if not wait(3+extratim, mainw):
                    err = -1
                subw.close()
                fftnam = "{0}/Y-fft.txt".format(mainw.progpath)
                subw = mainw.isAlreadyOpen(fftnam)
                if subw is not None:
                    subw.close()
    return err


def test_IR(mainw, extratim=0):
    """ Test the 'IRtrans' and 'IRabs' script commands.

    :param mainw: the application MainWindow
    :return: 0 if success, 1 if failure and -1 if interrupted by user.
    """
    err = 1
    if mainw.loadFile("{0}/selftests/IR.plt".format(mainw.testspath)):
        subw = mainw.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            msg = "#### Test of the 'IRabs' and 'IRtrans' script commands ####\n"
            msg += "# Test file : /selftests/IR.plt\n\n"
            pltw.datatext.setText(msg)
            if not wait(2, mainw):
                err = -1
            else:
                msg = "##### First testing 'IRabs' script command #####\n\n"
                pltw.datatext.setText(msg)
                err, ms = convertToAbs(pltw.blklst[0])
            if not err:
                pltw.updatePlot()
                if not wait(2+extratim, mainw):
                    err = -1
            if not err:
                msg = "##### Now testing 'IRtrans' script command #####\n\n"
                msg += "# End of the test"
                pltw.datatext.setText(msg)
                err, ms = convertToTrans(pltw.blklst[0])
                if not err:
                    pltw.updatePlot()
                    if not wait(3+extratim, mainw):
                        err = -1
            subw.close()
    return err


def test_line(mainw, extratim=0):
    """ Test the 'line' script command.

        This also test Cursor and Marker
    :param mainw: the application MainWindow
    :return: 0 if success, 1 if failure and -1 if interrupted by user.
    """
    err = 1
    if mainw.loadFile("{0}/selftests/line.plt".format(mainw.testspath)):
        subw = mainw.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            msg = "#### Test of the 'line' script commands ####\n"
            msg += "# Test file : /selftests/line.plt\n"
            pltw.datatext.setText(msg)
            if not wait(2, mainw):
                err = -1
            else:
                err = 0
            pltw.dcursor = dCursor(pltw)
            if pltw.dcursor.move(indx=270):
                msg += "# Set Cursor at X = 28.5\n"
                pltw.datatext.setText(msg)
                if not wait(3, mainw):
                    err = -1
            else:
                err = 1
            if not err:
                mainw.addMark()
                msg += "# Set a marker at cursor position\n"
                pltw.datatext.setText(msg)
                if not wait(3, mainw):
                    err = -1
            if not err:
                if pltw.dcursor.move(indx=414):
                    msg += "# Set Cursor at X = 33.0\n"
                    pltw.datatext.setText(msg)
                    if not wait(3, mainw):
                        err = -1
                else:
                    err = 1
            if not err:
               mainw.addMark()
               msg += "# Set a marker at cursor position\n"
               pltw.datatext.setText(msg)
               if not wait(3, mainw):
                    err = -1
            if not err:
               err, ms = line(pltw, 'Y')
               if not err:
                   pltw.updatePlot()
                   msg += "# Executing 'line Y' clears the second peak\n\n"
                   msg += "# End of the test"
                   pltw.datatext.setText(msg)
                   if not wait(4+extratim, mainw):
                       err = -1
            subw.close()
    return err


def test_linefit(mainw, extratim=0):
    """ Test the 'linefit' script command.

    :param mainw: the application MainWindow
    :return: 0 if success, 1 if failure and -1 if interrupted by user.
    """
    err = 1
    if mainw.loadFile("{0}/selftests/linefit.plt".format(mainw.testspath)):
        subw = mainw.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            msg = "#### Test of the 'linefit' script commands ####\n"
            msg += "# Test file : /selftests/linefit.plt\n"
            pltw.datatext.setText(msg)
            if not wait(3, mainw):
                err = -1
            else:
                err = 0
                pltw.dcursor = dCursor(pltw)
                if pltw.dcursor.move(indx=53):
                    msg += "# Set Cursor on the left side of the peak"
                    pltw.datatext.setText(msg)
                    if not wait(3, mainw):
                        err = -1
            if not err:
                err, result = lineFit(pltw, pltw.curvelist[0], 53, 1)
                if not err:
                    msg = "# Execute 'linefit Y' "
                    msg += "\n{}\n".format(result)
                    msg += "\n# End of the test"
                    pltw.datatext.setText(result)
                    if not wait(3+extratim, mainw):
                        err = -1
            subw.close()
    return err


def test_lineq(mainw, extratim=0):
    """ Test the 'lineq' script command.

    :param mainw: the application MainWindow
    :return: 0 if success, 1 if failure and -1 if interrupted by user.
    """
    err = 1
    if mainw.loadFile("{0}/selftests/lineq.plt".format(mainw.testspath)):
        subw = mainw.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            msg = "#### Test of the 'lineq' script commands ####\n"
            msg += "# Test file : /selftests/lineq.plt\n"
            pltw.datatext.setText(msg)
            if not wait(3+extratim, mainw):
                err = -1
            else:
                err = 0
                pltw.dcursor = dCursor(pltw)
                if pltw.dcursor.move(indx=20):
                    msg += "# Set Cursor at X = 1.0\n"
                    pltw.datatext.setText(msg)
                    if not wait(2, mainw):
                        err = -1
                else:
                    err = 1
            if not err:
                mainw.addMark()
                msg += "# Set a marker at cursor position\n"
                pltw.datatext.setText(msg)
                if not wait(2, mainw):
                    err = -1
            if not err:
                if pltw.dcursor.move(indx=60):
                    msg += "# Set Cursor at X = 3.0\n"
                    pltw.datatext.setText(msg)
                    if not wait(2, mainw):
                        err = -1
                else:
                    err = 1
            if not err:
                mainw.addMark()
                msg += "# Set a marker at cursor position\n"
                pltw.datatext.setText(msg)
                if not wait(2, mainw):
                    err = -1
            if not err:
                err, result = linEq(pltw, pltw.curvelist[0], 20, 60)
                x1 = pltw.blklst[0][0][20]
                y1 = pltw.blklst[0][1][20]
                x2 = pltw.blklst[0][0][60]
                y2 = pltw.blklst[0][1][60]
                pltw.lineList.append(lineSeg(x1, y1, x2, y2, 'red'))
                pltw.updatePlot()
                if not err:
                    msg = "# Execute 'lineq Y' \n"
                    msg += "{0}\n\n# End of the test".format(result)
                    pltw.datatext.setText(msg)
                    if not wait(3+extratim, mainw):
                        err = -1
            subw.close()
    return err


def test_mergeb(mainw, extratim=0):
    """ Test the 'mergeb' script command.

    :param mainw: the application MainWindow
    :return: 0 if success, 1 if failure and -1 if interrupted by user.
    """
    err = 1
    if mainw.loadFile("{0}/selftests/mergeb.txt".format(mainw.testspath)):
        subw = mainw.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            msg = "#### Test of the 'mergeb' script commands ####\n"
            msg += "# Test file : /selftests/mergeb.txt\n\n"
            msg += "# This file contains two data blocks with only one vector, \n"
            msg += "# The 'mergeb 1 2' command will merge these blocks such as \n"
            msg += "# there will be only one data block containing 2 vectors \n"
            pltw.datatext.setText(msg)
            if not wait(4, mainw):
                err = -1
            else:
                err, msg = mergeb(pltw, [1, 2])
            if not err:
                tmpnam = "{0}/selftests/tmp.txt".format(mainw.testspath)
                done = pltw.save(tmpnam)
                if done:
                    pltw.load(tmpnam)
                    msg += "# Execute 'mergeb 1 2' \n"
                    msg += "# End of the test"
                    pltw.datatext.setText(msg)
                    if not wait(4+extratim, mainw):
                        err = -1
                subw.close()
    return err


def test_ndec(mainw, extratim=0):
    """ Test the 'ndec' script command.

    :param mainw: the application MainWindow
    :return: 0 if success, 1 if failure and -1 if interrupted by user.
    """
    err = 1
    if mainw.loadFile("{0}/selftests/ndec.plt".format(mainw.testspath)):
        subw = mainw.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            mainw.tableTool()
            msg = "#### Test of the 'ndec' script commands ####\n"
            msg += "# Test file : /selftests/ndec.plt\n"
            msg += "# Display the data table"
            pltw.datatext.setText(msg)
            if not wait(5, mainw):
                err = -1
            else:
                err, ms = ndec(pltw, 'Y', 2)
                pltw.tabledlg.table.initTable()
            if not err:
                msg += "\n# Execute 'ndec Y 2' command"
                msg += "\n# Now, the Y values are rounded to 2 decimal place"
                msg += "\n\n# End of the test"
                pltw.datatext.setText(msg)
                if not wait(5+extratim, mainw):
                    err = -1
                pltw.tabledlg.close()
                subw.close()
    return err


def test_newv(mainw, extratim=0):
    """ Test the 'newv' script command.

    :param mainw: the application MainWindow
    :return: 0 if success, 1 if failure and -1 if interrupted by user.
    """
    err = 1
    mainw.fileNew()
    subw = mainw.getCurrentSubWindow()
    if subw is not None:
        pltw = subw.widget()
        msg = "#### Test of the 'newv' script commands ####\n"
        pltw.datatext.setText(msg)
        if not wait(1, mainw):
            err = -1
        else:
            err, ms = newV(pltw, "newv X 0,10,0.1")
        if not err:
            msg += "# Executing 'newv X 0,10,0.1' command\n"
            msg += "# This create a new vector X and\n"
            msg += "# a new data block for hosting X\n"
            msg += "\n# End of the test"
            pltw.datatext.setText(msg)
            pltw.displayInfo()
        if not wait(4 + extratim, mainw):
            err = -1
        pltw.dirty = False
        subw.close()
    return err


def test_onset(mainw, extratim=0):
    """ Test the 'linefit' script command.

    :param mainw: the application MainWindow
    :return: 0 if success, 1 if failure and -1 if interrupted by user.
    """
    err = 1
    if mainw.loadFile("{0}/selftests/onset.plt".format(mainw.testspath)):
        subw = mainw.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            msg = "#### Test of the 'onset' script commands ####\n"
            msg += "# Test file : /selftests/onset.plt\n"
            pltw.datatext.setText(msg)
            if not wait(2, mainw):
                err = -1
            else:
                err = 0
                pltw.dcursor = dCursor(pltw)
                if pltw.dcursor.move(indx=45):
                    msg += "# Set Cursor on the baseline\n"
                    pltw.datatext.setText(msg)
                    if not wait(2, mainw):
                        err = -1
                else:
                    err = 1
            if not err:
                mainw.addMark()
                msg += "# Set a marker at cursor position\n"
                pltw.datatext.setText(msg)
                if not wait(2, mainw):
                    err = -1
            if not err:
                if pltw.dcursor.move(indx=52):
                    msg += "# Set Cursor on the left side of the peak\n"
                    pltw.datatext.setText(msg)
                    if not wait(2, mainw):
                        err = -1
                else:
                    err = 1
            if not err:
                mainw.addMark()
                msg += "# Set a marker at cursor position\n"
                pltw.datatext.setText(msg)
                if not wait(2, mainw):
                    err = -1
            if not err:
                err, result = onset(pltw, pltw.curvelist[0], 45, 52)
                if not err:
                    msg += "# Execute 'onset Y' command"
                    msg += "{0}\n# End of the test".format(result)
                    pltw.datatext.setText(msg)
                    if not wait(5+extratim, mainw):
                        err = -1
            subw.close()
    return err


def test_PSD(mainw, extratim=0):
    """ Test the 'PSD' script command.

    :param mainw: the application MainWindow
    :return: 0 if success, 1 if failure and -1 if interrupted by user.
    """
    if mainw.progpath is None:
        # Because it will be impossible to create the temporary file
        return 1
    path = "{0}/selftests/PSD-iso.plt".format(mainw.testspath)
    if not mainw.loadFile(path):
        return 1
    subw = mainw.getCurrentSubWindow()
    if subw is None:
        return 1
    pltw = subw.widget()
    msg = "#### Test of the 'PSD' script commands ####\n"
    msg += "# Test file : /selftests/PSD-iso.plt\n"
    pltw.datatext.setText(msg)
    if not wait(3, mainw):
         err = -1
    else:
         psdnam = "{0}/PSD-PSD.plt".format(mainw.progpath)
         err, ms = PSDcalc(pltw.blklst[1], psdnam, 'D', "halsey")
    if not err:
        msg += "\n# Execute 'PSD D halsey' command"
        pltw.datatext.setText(msg)
        if not wait(2, mainw):
            err = -1
        subw.close()
    if not err:
        if mainw.loadFile(psdnam):
            subw = mainw.getCurrentSubWindow()
            if subw is not None:
                pltw = subw.widget()
                if not wait(4+extratim, mainw):
                    err = -1
                subw.close()
            else:
                err = 1
    return err


def test_revert(mainw, extratim=0):
    """ Test the 'revert' script command.

    :param mainw: the application MainWindow
    :return: 0 if success, 1 if failure and -1 if interrupted by user.
    """
    err = 1
    if mainw.loadFile("{0}/selftests/revert.plt".format(mainw.testspath)):
        subw = mainw.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            mainw.tableTool()
            msg = "#### Test of the 'revert' script commands ####\n"
            msg += "# Test file : /selftests/revert.plt\n"
            msg += "# Display the data table"
            pltw.datatext.setText(msg)
            if not wait(4, mainw):
                err = -1
            else:
                err, ms = revert(pltw, 'X')
                pltw.tabledlg.table.initTable()
            if not err:
                msg += "\n# After executing 'revert X' command"
                msg += "\n# The data are now in reverse order"
                msg += "\n\n# End of the test"
                pltw.datatext.setText(msg)
                if not wait(3+extratim, mainw):
                    err = -1
                pltw.tabledlg.close()
                subw.close()
    return err


def test_shift(mainw, extratim=0):
    """ Test the 'shift' script command.

        This also test Cursor and Marker
    :param mainw: the application MainWindow
    :return: 0 if success, 1 if failure and -1 if interrupted by user.
    """
    err = 1
    if mainw.loadFile("{0}/selftests/shift.plt".format(mainw.testspath)):
        subw = mainw.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            msg = "#### Test of the 'shift' script commands ####\n"
            msg += "# Test file : /selftests/shift.plt\n"
            pltw.datatext.setText(msg)
            if not wait(3, mainw):
                err = -1
            else:
                err = 0
            pltw.dcursor = dCursor(pltw)
            if pltw.dcursor.move(indx=20):
                msg += "# Set Cursor at X = 2\n"
                pltw.datatext.setText(msg)
                if not wait(2, mainw):
                    err = -1
            else:
                err = 1
            if not err:
                mainw.addMark()
                msg += "# Set a marker at cursor position\n"
                pltw.datatext.setText(msg)
                if not wait(2, mainw):
                    err = -1
            if not err:
                if pltw.dcursor.move(indx=60):
                    msg += "# Set Cursor at X = 6\n"
                    pltw.datatext.setText(msg)
                    if not wait(2, mainw):
                        err = -1
                else:
                    err = 1
            if not err:
               mainw.addMark()
               msg += "# Set a marker at cursor position\n"
               pltw.datatext.setText(msg)
               if not wait(2, mainw):
                    err = -1
            if not err:
               err, ms = shift(pltw, pltw.curvelist[0], -0.6, 20, 60)
               if not err:
                   pltw.updatePlot()
                   msg += "# Execute 'shift Y -0.6' command"
                   msg += "\n# End of the test"
                   pltw.datatext.setText(msg)
                   if not wait(3+extratim, mainw):
                       err = -1
            subw.close()
    return err


def test_shrink(mainw, extratim=0):
    """ Test the 'shrink' script command.

    :param mainw: the application MainWindow
    :return: 0 if success, 1 if failure and -1 if interrupted by user.
    """
    err = 1
    if mainw.loadFile("{0}/selftests/shrink.plt".format(mainw.testspath)):
        subw = mainw.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            msg = "#### Test of the 'shrink' script commands ####\n"
            msg += "# Test file : /selftests/shrink.plt\n"
            pltw.datatext.setText(msg)
            if not wait(3, mainw):
                err = -1
            else:
                msg += "# Execute the command 'shrink TG 5'\n"
                err, ms = shrink(pltw, 'TG', 5)
            if not err:
                msg += "\n# {0}\n\n# End of the test".format(ms)
                pltw.datatext.setText(msg)
                if not wait(4+extratim, mainw):
                    err = -1
                subw.close()
    return err


def test_sort(mainw, extratim=0):
    """ Test the 'sort' script command.

    :param mainw: the application MainWindow
    :return: 0 if success, 1 if failure and -1 if interrupted by user.
    """
    err = 1
    if mainw.loadFile("{0}/selftests/sort.plt".format(mainw.testspath)):
        subw = mainw.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            msg = "#### Test of the 'sort' script commands ####\n"
            msg += "# Test file : /selftests/sort.plt\n"
            msg += "# This is the curve of Y = X*X but X values are not sorted."
            pltw.datatext.setText(msg)
            if not wait(4, mainw):
                err = -1
            else:
                err, ms = sort(pltw, 'X')
            if not err:
                pltw.updatePlot()
                msg += "\n# After executing 'sort X' command"
                msg += "\n\n# End of the test"
                pltw.datatext.setText(msg)
                if not wait(4+extratim, mainw):
                    err = -1
                subw.close()
    return err


def test_stats(mainw, extratim=0):
    """ Test the 'stats' script command.

    :param mainw: the application MainWindow
    :return: 0 if success, 1 if failure and -1 if interrupted by user.
    """
    err = 1
    if mainw.loadFile("{0}/selftests/stats.plt".format(mainw.testspath)):
        subw = mainw.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            msg = "#### Test of the 'stats' script commands ####\n"
            msg += "# Test file : /selftests/stats.plt\n"
            msg += "# About to execute 'stats Y' command"
            pltw.datatext.setText(msg)
            if not wait(3, mainw):
                err = -1
            else:
                err, msg = stats(pltw, 'Y')
            if not err:
                pltw.datatext.setText(msg)
                if not wait(5+extratim, mainw):
                    err = -1
                subw.close()
    return err


def test_swapv(mainw, extratim=0):
    """ Test the 'swapv' script command.

    :param mainw: the application MainWindow
    :return: 0 if success, 1 if failure and -1 if interrupted by user.
    """
    err = 1
    if mainw.loadFile("{0}/selftests/swapv.plt".format(mainw.testspath)):
        subw = mainw.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            msg = "#### Test of the 'swapv' script commands ####\n"
            msg += "# Test file : /selftests/swapv.plt"
            pltw.datatext.setText(msg)
            if not wait(3, mainw):
                err = -1
            else:
                err, ms = swapv(pltw, 'X', 'Y')
            if not err:
                pltw.updatePlot()
                msg += "\n# After executing 'swapv X Y' command"
                msg += "\n\n# End of the test"
                pltw.datatext.setText(msg)
                if not wait(3+extratim, mainw):
                    err = -1
                subw.close()
    return err


# ------------------------------------------------------------------------

tstnam = ["area", "BET", "clipup & clipdn", "clipx", "delb", "deldupx", "delv",
          "despike", "fft", "IR", "line", "linefit", "lineq", "mergeb",
          "ndec", "newv", "onset", "PSD", "revert", "shift", "shrink", "sort",
          "stats", "swapv"]

tstfunc = [test_area, test_BET, test_clipupdn, test_clipx, test_delb,
           test_deldupx, test_delv, test_despike, test_fft, test_IR, test_line,
           test_linefit, test_lineq, test_mergeb, test_ndec, test_newv,
           test_onset, test_PSD, test_revert, test_shift, test_shrink,
           test_sort, test_stats, test_swapv ]


def runTests(mainw):
    """

    :param mainw:
    :return:
    """
    dlg = testDlg(mainw)
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
            err = func(mainw)
            if err == -1:
                # user interruption
                break
            if err == 0:
                res = "passed"
            else:
                res = "failed"
            result.append("{0} test {1}".format(tstnam[i], res))
        msg = '\n'.join(result)
    else:
        err = tstfunc[pos - 1](mainw, extratim=3)
        if err == -1:
            res = "stopped by user"
        elif err == 0:
            res = "passed"
        else:
            res = "failed"
        msg = "{0} test : {1}".format(tstnam[pos - 1], res)

    title = "Test results"
    QtWidgets.QMessageBox.warning(mainw, title, msg)

