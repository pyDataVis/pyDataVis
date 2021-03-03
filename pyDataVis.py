# pyDataVis MainWindow

import sys, os, csv, platform, shutil, inspect
from urllib.request import urlopen
import copy
import numpy as np
import pandas as pd

from PyQt5.QtCore import ( QFile, QFileInfo, QSettings, QSignalMapper,
                           QTimer, QVariant, Qt, QPoint )
from PyQt5 import QtGui, QtWidgets

from plotWindow import plotWin, dCursor
from convert import convSelector
from dataTable import tableDlg
from toolsDialogs import (smoothDlg, splinSmoothDlg, ALS_SmoothDlg,
                              modelSelectDlg, fitCurveDlg, pkFindDlg, pkFitDlg,
                              interpolDlg, baselineDlg, noiseDlg, deNoiseDlg)
from script import script
from utils import (checkURL, cpyFromURL, round_to_n, getDataFromUrl,
                                 copyFiles, textToData, exportToVeusz)
from tests import runTests, runAllTests


__version__ = "1.5.0"

# - settingsDlg class ------------------------------------------------------------

class settingsDlg(QtWidgets.QDialog):
    def __init__(self, parent=None):
        """ Settings dialog.

        :param parent: pyDataVis MainWindow.
        """
        super (settingsDlg, self).__init__(parent)

        self.parent = parent

        # Application font size
        appFontlab = QtWidgets.QLabel("Application font size")
        self.appFontComboBox = QtWidgets.QComboBox(self)
        sizlst = range(6, 20)  # list of font size between 6 and 20
        self.appFontlist = [str(i) for i in sizlst]
        self.appFontComboBox.addItems(self.appFontlist)
        # Text editor font size
        txtFontlab = QtWidgets.QLabel("Text editor font size")
        self.txtFontComboBox = QtWidgets.QComboBox(self)
        sizlst = range(6, 20)  # list of font size between 6 and 20
        self.txtFontlist = [str(i) for i in sizlst]
        self.txtFontComboBox.addItems(self.txtFontlist)
        # Chart font size
        chartFontlab = QtWidgets.QLabel("Chart font size")
        self.chartFontComboBox = QtWidgets.QComboBox(self)
        self.chartFontlist = ['small', 'medium', 'large']
        self.chartFontComboBox.addItems(self.chartFontlist)
        # Buttons
        applyBtn = QtWidgets.QPushButton("Apply")
        okBtn = QtWidgets.QPushButton("OK")
        cancelBtn = QtWidgets.QPushButton("Cancel")

        # set the layout
        vbox = QtWidgets.QVBoxLayout()
        hbox1 = QtWidgets.QHBoxLayout()
        hbox1.addWidget(appFontlab)
        hbox1.addWidget(self.appFontComboBox)
        hbox2 = QtWidgets.QHBoxLayout()
        hbox2.addWidget(txtFontlab)
        hbox2.addWidget(self.txtFontComboBox)
        hbox3 = QtWidgets.QHBoxLayout()
        hbox3.addWidget(chartFontlab)
        hbox3.addWidget(self.chartFontComboBox)
        hbox4 = QtWidgets.QHBoxLayout()
        hbox4.addWidget(applyBtn)
        hbox4.addWidget(okBtn)
        hbox4.addWidget(cancelBtn)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)
        vbox.addLayout(hbox4)
        self.setLayout(vbox)

        # Connect buttons to callback functions
        applyBtn.clicked.connect(self.apply)
        okBtn.clicked.connect(self.validate)
        cancelBtn.clicked.connect(self.reject)
        self.setWindowTitle('Settings')
        self.initDlg()


    def initDlg(self):
        """ Initialize the dialog.

        :return: nothing
        """
        self.appFontSiz = self.parent.appfontsiz
        cbidx = self.appFontlist.index(str(self.appFontSiz))
        self.appFontComboBox.setCurrentIndex(cbidx)

        self.txtFontSiz = self.parent.txteditfontsiz
        cbidx = self.txtFontlist.index(str(self.txtFontSiz))
        self.txtFontComboBox.setCurrentIndex(cbidx)

        self.chartFontSiz = self.parent.chartfontsiz
        cbidx = self.chartFontlist.index(str(self.chartFontSiz))
        self.chartFontComboBox.setCurrentIndex(cbidx)


    def apply(self):
        """ Callback function when user has clicked on Apply button.

        :return: nothing
        """
        # Change application font size
        self.appFontSiz = int(str(self.appFontComboBox.currentText()))
        font = self.parent.app.font()
        font.setPointSize(self.appFontSiz)
        self.parent.app.setFont(font)

        # Change QTextEdit font size in all the plotWin sub windows
        self.txtFontSiz = int(str(self.txtFontComboBox.currentText()))
        self.parent.txteditfont.setPointSize(self.txtFontSiz)

        # Change chart font size
        self.chartFontSiz = self.chartFontComboBox.currentText()
        self.parent.chartfontsiz = self.chartFontSiz

        for subw in self.parent.mdi.subWindowList():
            pltw = subw.widget()
            pltw.setTextFont(self.parent.txteditfont)
            pltw.updatePlot()


    def validate(self):
        """ Callback function when user has clicked on OK button.

        :return: nothing
        """
        self.apply()
        self.parent.appfontsiz = self.appFontSiz
        self.parent.txteditfontsiz = self.txtFontSiz
        self.parent.chartfontsiz = self.chartFontSiz
        self.hide()



# - infoDlg class ------------------------------------------------------------

class infoDlg(QtWidgets.QDialog):
    def __init__(self, parent=None, type=None):
        """ Information dialog.

        :param parent: pyDataVis MainWindow.
        :param log: True if this dialog is used to display the logfile.
        """
        super (infoDlg, self).__init__(parent)

        self.parent = parent
        self.text = QtWidgets.QTextEdit(self)
        self.text.setCurrentFont(self.parent.txteditfont)
        self.fontMetrics = QtGui.QFontMetrics(self.parent.txteditfont)
        self.ini = True
        hbox = QtWidgets.QHBoxLayout()
        hbox.addStretch(1)
        if type == "log":
            title = "LogFile"
            clearBtn = QtWidgets.QPushButton("Clear")
            okBtn = QtWidgets.QPushButton("Save")
            cancelBtn = QtWidgets.QPushButton("Cancel")
            clearBtn.clicked.connect(self.clearLog)
            cancelBtn.clicked.connect(self.reject)
            okBtn.clicked.connect(self.validate)
            hbox.addWidget(clearBtn)
            hbox.addWidget(cancelBtn)
        elif type == "info":
            title = "Information"
            self.text.setReadOnly(True)
            okBtn = QtWidgets.QPushButton("OK")
            okBtn.clicked.connect(self.accept)
        elif type == "about":
            title = "About pyDataVis"
            self.text.setReadOnly(True)
            iconLabel = QtWidgets.QLabel(self)
            logopath = os.path.join(parent.progpath, "icons", "logo.jpg")
            if not os.path.exists(logopath):
                url = 'https://github.com/pyDataVis/pyDataVis.github.io/raw/main/img/logo.jpg'
                if checkURL(url):
                    path = os.path.dirname(logopath)
                    if not os.path.exists(path):
                        os.mkdir(path)
                    cpyFromURL(url, logopath)
            if os.path.exists(logopath):
                pixmap = QtGui.QPixmap(logopath)
                iconLabel.setPixmap(pixmap)
                iconLabel.setAlignment(Qt.AlignCenter)
            okBtn = QtWidgets.QPushButton("OK")
            licenseBtn = QtWidgets.QPushButton("Show license")
            okBtn.clicked.connect(self.accept)
            licenseBtn.clicked.connect(self.showLicense)
            hbox.addWidget(licenseBtn)

        hbox.addWidget(okBtn)
        vbox = QtWidgets.QVBoxLayout()
        if type == "about":
            vbox.addWidget(iconLabel)
        vbox.addWidget(self.text)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        self.setWindowTitle(title)
        self.text.textChanged.connect(self.onChanged)

    def onChanged(self):
        if self.ini:
            self.ini = False
            mainwh = self.parent.frameGeometry().height()
            textSize = self.fontMetrics.size(0, self.text.toPlainText())
            w = textSize.width() + 30
            h = textSize.height() + 30
            if h > mainwh:
                h = int(mainwh * 0.9)
            self.text.setMinimumSize(w, h)
            self.text.setMaximumSize(w, h)
            self.text.resize(w, h)
            self.text.moveCursor(QtGui.QTextCursor.End)

    def clearLog(self):
        self.text.clear()

    def validate(self):
        path = "{0}/logfile.txt".format(self.parent.progpath)
        file = open(path, 'w')
        file.write(self.text.toPlainText())
        self.hide()

    def showLicense(self):
        fo = None
        licpath = os.path.join(self.parent.progpath, "LICENSE")
        if os.path.isfile(licpath):
            fo = open(licpath, 'r')
            txt = fo.read()
            fo.close()
        else:
            url = "https://raw.githubusercontent.com/pyDataVis/pyDataVis.github.io/main/LICENSE"
            if checkURL(url):
                fo = urlopen(url)
                txt = fo.read().decode('utf-8')
                fo.close()
                cpyFromURL(url, licpath)
        if fo is not None:
            msg = QtWidgets.QMessageBox()
            msg.setFont(self.parent.txteditfont)
            msg.setText(txt)
            msg.setWindowTitle("pyDataVis License")
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg.exec_()


#- MainWindow --------------------------------------------------------------

class MainWindow(QtWidgets.QMainWindow):
    Xcpy = None                 # Store X data when a curve is copied
    Ycpy = None                 # Store Y data when a curve is copied
    labXcpy = None              # Store the name of the vector X
    labYcpy = None              # Store the name of the vector Y

    def __init__(self, datapath, parent = None):
        super(MainWindow, self).__init__(parent)

        self.datapath = datapath
        self.testspath = os.path.join(self.datapath, "tests")
        # Find the location of the program folder
        path = inspect.getfile(inspect.currentframe())
        self.progpath, f = os.path.split(path)
        path = os.path.join(self.progpath, "pyDataVis.py")
        if not os.path.exists(path):
            self.progpath = None

        self.app = QtWidgets.QApplication.instance()
        self.mdi = QtWidgets.QMdiArea()
        # Enable drag & drop onto the GUI
        self.setAcceptDrops(True)
        self.setCentralWidget(self.mdi)

        # Adapt the MainWindow size to the screen resolution
        screen = self.app.primaryScreen()
        self.scrsize = screen.size()
        ww = int(self.scrsize.width() * 0.45)
        wh = int(self.scrsize.height() * 0.7)
        self.resize(ww, wh)
        # Adapt the Application font size to the screen resolution
        font = self.app.font()
        if self.scrsize.width() <= 1920:
            fntsiz = 8
        else:
            fntsiz = 13
        font.setPointSize(fntsiz)
        self.app.setFont(font)
        self.appfontsiz = fntsiz
        # Adapt the TextEdit font size to the screen resolution
        self.txteditfont = QtGui.QFont('Noto Sans')
        if platform.system() == "Windows":
            fntsiz = 10
        elif platform.system() == "Linux":
            if self.scrsize.width() <= 1920:
                fntsiz = 8
            else:
                fntsiz = 12
        else:
            fntsiz = 10
        self.txteditfont.setPointSize(fntsiz)
        self.txteditfontsiz = fntsiz
        self.chartfontsiz = "medium"

        self.numpltw = 0         # Store the number of plotWin
                                 # The following data are used for undo
        self.pltwcpy = None      # Store a copy of current plotWin
        self.datacpy = None      # Store a copy of list of numerical arrays
        self.curvelistcpy = None # Store a copy of curvelist
        self.dirtycpy = None
        self.create_actions()
        self.load_settings()
        self.test = False        # is set to True during testing
        self.smoothDlg = None
        self.splinSmoothDlg = None
        self.interpolDlg = None
        self.helpDlg = None
        self.fitmodels = ('Polynomial','Exponential', 'Logarithm',
                          'Arrhenius', 'Rheo Power Law',
                          'Rheo Herschel-Bulkley', 'Sigmoid')
        self.smoothtyp = 1       # Type for smoothing (0=MA, 1=SG)
        self.smoothFilter = 5
        self.smoothpass = 1
        self.fitmodel = 0
        self.pkfitguess = None
        self.keyb = None
        self.statusbar = self.statusBar()
        self.statusbar.setSizeGripEnabled(False)
        msg = "Welcome to {0}".format(self.app.applicationName())
        self.statusbar.showMessage(msg, 5000)
        self.updateWindowMenu()
        self.setWindowTitle(self.app.applicationName())
        iconpath = os.path.join(self.datapath, "icons", "icon.ico")
        if not os.path.isfile(iconpath):
            # Try to load data files from GitHub
            url = "https://github.com/pyDataVis/pyDataVis/archive/main.zip"
            errmsg = self.getDataFromUrl(url)
            if errmsg:
                title = "Fail to get data from GitHub"
                QtWidgets.QMessageBox.warning(self, title, errmsg)
        if os.path.isfile(iconpath):
            self.setWindowIcon(QtGui.QIcon(iconpath))
        QTimer.singleShot(0, self.loadFiles)
        self.updateUI()
        # Update User Interface each time a new sub window is activated
        self.mdi.subWindowActivated.connect(self.updateUI)
        if platform.system() == "Darwin":
            self.mdi.setFocus()


    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            event.accept()
            links = []
            for url in event.mimeData().urls():
                links.append(url.toLocalFile())
            for url in links:
                if os.path.exists(url):
                    if QFileInfo(url).isFile():
                        self.loadFile(str(url))
                        QtWidgets.QApplication.processEvents()
        else:
            event.ignore()


    def create_actions(self):
        self.fileNewAction = self.createAction("&New...", self.fileNew,
                QtGui.QKeySequence.New, None,
                "Create a new empty pyDataVis window")
        self.fileOpenAction = self.createAction("&Open...", self.fileOpen,
                QtGui.QKeySequence.Open, None,
                "Open a text data file")
        self.fileAppendAction = self.createAction("Append...", self.fileAppend,
                None, None,
                "Append a text data file")
        self.fileImportAction = self.createAction("Import from spreadsheet",
                self.fileImport, None, None,
                "Import data from a spreadsheet file")
        self.fileSettingsAction = self.createAction("Settings", self.fileSettings,
                None, None, "Change settings")
        self.fileSaveAction = self.createAction("&Save data", self.fileSave,
                QtGui.QKeySequence.Save, "filesave",
                "Save the data in a file")
        self.fileSaveAsAction = self.createAction("Save data &As...",
                self.fileSaveAs, QtGui.QKeySequence.SaveAs, None,
                tip="Save the current data in a file using a new filename")
        self.fileSaveTextAction = self.createAction("Save text",
                self.fileSaveText, None, None,
                "Save the content of the text editor in a file")
        self.fileExportVeuszAction = self.createAction("Export to Veusz", self.fileExportVeusz,
                None, None,
                "Export data to Veusz")
        self.fileExportExcelAction = self.createAction("Export to Excel", self.fileExportExcel,
                None, None,
                "Export data to Excel")
        self.fileExportCSVAction = self.createAction("Export as CSV", self.fileExportCSV,
                None, None,
                "Export data as CSV")
        self.fileUpdateFromTextAction = self.createAction("Update from text",
                self.fileUpdateFromText, None, None,
                 "Update plot & data with the content of the text editor")
        self.fileUpdateFromDataAction = self.createAction("Update from data",
                self.fileUpdateFromData, None, None,
                "Update text editor from numerical data")
        self.fileViewLogAction = self.createAction("View log",
                self.fileViewLogFile, None, None,
                "View the log file")
        self.fileQuitAction = self.createAction("&Quit", self.close,
                "Ctrl+Q", "filequit", "Close the application")

        self.curvCutAction = self.createAction("Cut", self.curvCut,
                "Ctrl+Shift+X", None,
                "Copy a curve in memory then delete it")
        self.curvCopyAction = self.createAction("Copy", self.curvCopy,
                "Ctrl+Shift+C", None,
                "Copy a curve in memory")
        self.curvDuplicateAction = self.createAction("Duplicate", self.curvDuplicate,
                "Ctrl+Shift+B", None,
                "Duplicate a curve")
        self.curvSaveInFileAction = self.createAction("Save in file",
                self.curvSaveInFile, None, None,
                "Save a curve in a new file")
        self.curvPasteAction = self.createAction("Paste", self.curvPaste,
                "Ctrl+Shift+V", None,
                "Paste the curve stored in memory")
        self.curvDelAction = self.createAction("Delete", self.curvDelete,
                "Ctrl+Shift+D", None,
                "Delete a curve")

        self.cursorUpAction = self.createAction("Cursor &Up", self.cursorUp,
                "Ctrl+U", None,
                "Move the cursor on the previous curve")
        self.cursorDnAction = self.createAction("Cursor &Down", self.cursorDn,
                "Ctrl+D", None,
                "Move the cursor on the next curve")
        self.cursorLeftAction = self.createAction("Cursor Left",
                self.cursorLeft, "Ctrl+Left", None,
                "Move the cursor on the previous data point of the curve")
        self.cursorRightAction = self.createAction("Cursor Right",
                self.cursorRight, "Ctrl+Right", None,
                "Move the cursor on the next data point of the curve")
        self.cursorFirstAction = self.createAction("Cursor &First",
                self.cursorFirst, "Ctrl+F", None,
                "Move the cursor on the first point of the curve")
        self.cursorLastAction = self.createAction("Cursor &Last",
                self.cursorLast, "Ctrl+L", None,
                "Move the cursor on the last point of the curve")
        self.addMarkAction = self.createAction("Add a &Mark", self.addMark,
                "Ctrl+M", None,
                "Add or move a mark at the cursor position")
        self.clearMarksAction = self.createAction("Remove all marks",
                self.clearMarks, "Ctrl+R", None,
                "Remove cursor and marks")

        self.convertCIFAction = self.createAction("CIF", self.convert,
                None, None,
                "Generate diffraction pattern from CIF data")
        self.convertDATAction = self.createAction("DAT", self.convert,
                None, None,
                "Convert .DAT diffraction ASCII file format")
        self.convertPRFAction = self.createAction("PRF", self.convert,
                None, None,
                "Convert .PRF file generated by FullProf")
        self.convertReshapeAction = self.createAction("Reshape", self.convert,
                None, None,
                "Change the shape (lines, columns) of a data file")
        self.convertTransposeAction = self.createAction("Transpose", self.convert,
                None, None,
                "Reverse the lines and the columns of a data file")
        self.convert1DAction = self.createAction("1D->2D", self.convert,
                None, None,
                "Add a new vector with the number of the point to a 1D data file")

        self.scriptLoadAction = self.createAction("Load script",
                self.loadScript, None, None,
                "Load a script from file")
        self.scriptSaveAction = self.createAction("Save script",
                self.saveScript, None, None,
                "Save the current script in a file")
        self.scriptRunAction = self.createAction("&Execute a script",
                self.runScript, "Ctrl+E", None,
                "Execute the current script")
        self.scriptRunPyAction = self.createAction("&Execute a python script",
                self.runPyScript, None, None,
                "Execute a Python script")
        self.scriptClearAction = self.createAction("Clear script",
                self.clearScript, "Ctrl+K", None,
                "Clear the current script")
        self.scriptUndoAction = self.createAction("Undo",
                self.undoLast, None, None,
                "Undo the previous command")

        self.toolsSmoothAction = self.createAction("Smoothing",
                self.smoothTool, None, None,
                "Smooth a curve")
        self.toolsSplinSmoothAction = self.createAction("Spine Smoothing",
                self.splinSmoothTool, None, None,
                "Smooth a curve using spine functions")
        self.toolsALS_SmoothAction = self.createAction("ALS Smoothing",
                self.ALS_SmoothTool, None, None,
                "Smooth a curve")
        self.toolsCurveFitAction = self.createAction("Curve Fitting", self.fitCurveTool,
                None, None,
                "Fit a curve")
        self.toolsFindPkAction = self.createAction("Peak Finding", self.findPkTool,
                None, None,
                "Find peaks")
        self.toolsFitPkAction = self.createAction("Peak Fitting", self.fitPkTool,
                None, None,
                "Fit peaks")
        self.toolsInterpAction = self.createAction("Interpolation",
                self.interpolTool, None, None,
                "Data interpolation")
        self.toolsBaselineAction = self.createAction("Baseline",
                self.baselineTool, None, None,
                "Baseline correction")
        self.toolsNoiseAction = self.createAction("Add Noise",
                self.noiseTool, None, None,
                "Add noise to data")
        self.toolsdeNoiseAction = self.createAction("Remove Noise",
                self.deNoiseTool, None, None,
                "Remove moise from data")
        self.toolsTableAction = self.createAction("Data &Table",
                self.tableTool, "Ctrl+T", None,
                "Show data table")

        self.windowCascadeAction = self.createAction("Cascade",
                self.mdi.cascadeSubWindows)
        self.windowTileAction = self.createAction("Tile",
                self.mdi.tileSubWindows)
        self.windowCloseAction = self.createAction("Close",
                self.mdi.closeActiveSubWindow, QtGui.QKeySequence.Close)
        self.windowMapper = QSignalMapper(self)
        self.windowMapper.mapped.connect(self.mdi.setActiveSubWindow)

        helpAction = self.createAction("Help", self.help,
                None, None, "Open pyDataVis manual")
        helpCurveTestAction = self.createAction("Run curve tests", self.runSelfTests,
                None, None, "Test curves manipulation")
        helpScriptTestAction = self.createAction("Run script tests", self.runSelfTests,
                None, None, "Test script commands")
        helpIOTestAction = self.createAction("Run I/O tests", self.runSelfTests,
                None, None, "Test Input/Output")
        helpConvTestAction = self.createAction("Run Convert tests", self.runSelfTests,
                None, None, "Test convert options")
        helpToolsTestAction = self.createAction("Run Tools tests", self.runSelfTests,
                None, None, "Test Tools options")
        helpAllTestsAction = self.createAction("Run all tests", self.runSelfTests,
                None, None, "Run all the tests")
        self.helpUpdateAction = self.createAction("Update from GitHub", self.updateFromGitHub,
                None, None, "Download data from GitHub")
        helpAboutAction = self.createAction("About", self.helpAbout,
                None, None, "About pyDataVis")

        fileMenu = self.menuBar().addMenu("&File")
        self.addActions(fileMenu, (self.fileNewAction, self.fileOpenAction,
                self.fileAppendAction, self.fileImportAction,
                self.fileSaveAction, self.fileSaveAsAction,
                self.fileSaveTextAction, None, self.fileExportVeuszAction,
                self.fileExportExcelAction, self.fileExportCSVAction,
                None, self.fileSettingsAction,
                None, self.fileUpdateFromTextAction,
                self.fileUpdateFromDataAction, None,
                self.fileViewLogAction, None, self.fileQuitAction))
        curveMenu = self.menuBar().addMenu("&Curve")
        self.addActions(curveMenu, (self.curvCutAction,
                self.curvCopyAction, self.curvDuplicateAction,
                self.curvSaveInFileAction, self.curvPasteAction,
                self.curvDelAction))
        marksMenu = self.menuBar().addMenu("&Marks")
        self.addActions(marksMenu, (self.cursorUpAction,
                self.cursorDnAction, self.cursorLeftAction,
                self.cursorRightAction, self.cursorFirstAction,
                self.cursorLastAction, None,
                self.addMarkAction, self.clearMarksAction))
        convertMenu = self.menuBar().addMenu("&Convert")
        self.addActions(convertMenu, (self.convertCIFAction,
                self.convertDATAction, self.convertPRFAction, None,
                self.convertReshapeAction, self.convertTransposeAction,
                self.convert1DAction ))
        scriptMenu = self.menuBar().addMenu("&Script")
        self.addActions(scriptMenu, (self.scriptLoadAction,
                self.scriptSaveAction, self.scriptRunAction,
                self.scriptRunPyAction, None, self.scriptClearAction,
                None, self.scriptUndoAction))
        toolsMenu = self.menuBar().addMenu("&Tools")
        self.addActions(toolsMenu, (self.toolsSmoothAction,
                self.toolsSplinSmoothAction, self.toolsALS_SmoothAction,
                self.toolsCurveFitAction, self.toolsFindPkAction,
                self.toolsFitPkAction, self.toolsInterpAction,
                self.toolsBaselineAction, self.toolsNoiseAction,
                self.toolsdeNoiseAction,
                None, self.toolsTableAction))
        self.windowMenu = self.menuBar().addMenu("&Window")
        self.windowMenu.aboutToShow.connect(self.updateWindowMenu)
        helpMenu = self.menuBar().addMenu("&Help")
        self.addActions(helpMenu, (helpAction, None,
                                   helpCurveTestAction,helpScriptTestAction,
                                   helpIOTestAction, helpConvTestAction,
                                   helpToolsTestAction,
                                   helpAllTestsAction, None,
                                   self.helpUpdateAction, None, helpAboutAction))


    def load_settings(self):
        """ Load settings from pyDataVis.conf

        :return: nothing
        """
        settings = QSettings()
        settings.beginGroup("mainwindow")
        if settings.contains("size"):
            self.resize(settings.value('size'))
            self.move(settings.value('position'))
        settings.endGroup()
        settings.beginGroup("font")
        if settings.contains("appfontsiz"):
            font = self.app.font()
            fntsiz = int(settings.value('appfontsiz'))
            font.setPointSize(fntsiz)
            self.app.setFont(font)
            self.appfontsiz = fntsiz
            fntsiz = int(settings.value('txteditfontsiz'))
            self.txteditfont.setPointSize(fntsiz)
            self.txteditfontsiz = fntsiz
            self.chartfontsiz = settings.value('chartfontsiz', "medium")
        settings.endGroup()


    def createAction(self, text, slot=None, shortcut=None, icon=None,
                     tip=None, checkable=False):
        action = QtWidgets.QAction(text, self)
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            action.triggered.connect(slot)
        if checkable:
            action.setCheckable(True)
        return action


    def addActions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)


    def closeEvent(self, event):
        title = self.app.applicationName() + " -- Save Error"
        failures = []
        for subw in self.mdi.subWindowList():
            pltw = subw.widget()
            if pltw.dirty:
                if (QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No) == \
                        QtWidgets.QMessageBox.Yes:
                    try:
                        pltw.save()
                    except IOError as err:
                        failures.append(str(err))
        if (failures and
            QtWidgets.QMessageBox.warning(self, title,
                    "Failed to save{0}\nQuit anyway?".format(
                    "\n\t".join(failures)),
                    QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No) ==
                        QtWidgets.QMessageBox.No):
            event.ignore()
            return
        self.save_settings()
        self.mdi.closeAllSubWindows()
        self.updateUI()


    def save_settings(self):
        """ Save settings in pyDataVis.conf file.

        :return: nothing
        """
        settings = QSettings()
        settings.beginGroup("mainwindow")
        settings.setValue('size', self.size())
        settings.setValue('position', self.pos())
        settings.endGroup()
        settings.beginGroup("font")
        settings.setValue('appfontsiz', self.appfontsiz)
        settings.setValue('txteditfontsiz', self.txteditfontsiz)
        settings.setValue('chartfontsiz', self.chartfontsiz)
        settings.endGroup()
        settings.beginGroup("files")
        subw = self.mdi.currentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            if not pltw.filename.startswith("Unnamed"):
                settings.setValue("lastfile", QVariant(pltw.filename))
        else:
            settings.remove("lastfile")
        settings.endGroup()



    def updateUI(self):
        """ Update the state of menu items

        :return: nothing
        """
        state = (self.numpltw > 0)
        self.fileAppendAction.setEnabled(state)
        self.fileSaveAction.setEnabled(state)
        self.fileSaveAsAction.setEnabled(state)
        self.fileSaveTextAction.setEnabled(state)
        self.fileUpdateFromTextAction.setEnabled(state)
        self.fileUpdateFromDataAction.setEnabled(state)
        self.curvPasteAction.setEnabled(state and MainWindow.Ycpy is not None)
        self.scriptLoadAction.setEnabled(state)
        self.scriptSaveAction.setEnabled(state)
        self.scriptRunAction.setEnabled(state)
        self.scriptRunPyAction.setEnabled(state)
        self.scriptClearAction.setEnabled(state)
        state2 = state and self.datacpy is not None
        self.scriptUndoAction.setEnabled(state2)
        subw = self.getCurrentSubWindow()
        if state and subw is not None:
            pltw = subw.widget()
            state2 = pltw.blklst is not None and (len(pltw.curvelist) > 0)
        else:
            pltw = None
            state2 = False
        self.fileExportVeuszAction.setEnabled(state2)
        self.fileExportExcelAction.setEnabled(state2)
        self.fileExportCSVAction.setEnabled(state2)
        self.curvCopyAction.setEnabled(state2)
        self.curvDuplicateAction.setEnabled(state2)
        self.curvSaveInFileAction.setEnabled(state2)
        self.curvCutAction.setEnabled(state2)
        self.curvDelAction.setEnabled(state2)
        self.toolsSmoothAction.setEnabled(state2)
        self.toolsSplinSmoothAction.setEnabled(state2)
        self.toolsALS_SmoothAction.setEnabled(state2)
        self.toolsCurveFitAction.setEnabled(state2)
        self.toolsFindPkAction.setEnabled(state2)
        self.toolsFitPkAction.setEnabled(state2)
        self.toolsInterpAction.setEnabled(state2)
        self.toolsBaselineAction.setEnabled(state2)
        self.toolsNoiseAction.setEnabled(state2)
        self.toolsdeNoiseAction.setEnabled(state2)
        self.toolsTableAction.setEnabled(state2)
        state3 = (pltw is not None) and (pltw.datatext.toPlainText() != "")
        self.convertCIFAction.setEnabled(state3)
        self.convertPRFAction.setEnabled(state3)
        self.convertDATAction.setEnabled(state3)
        self.convertReshapeAction.setEnabled(state3)
        self.convertTransposeAction.setEnabled(state3)
        self.convert1DAction.setEnabled(state3)
        if state2 and pltw.dcursor is not None:
            state2 = bool(pltw.dcursor.ic > 0)
            if pltw.xascending:
                self.cursorLeftAction.setEnabled(state2)
                self.cursorFirstAction.setEnabled(state2)
            else:
                self.cursorRightAction.setEnabled(state2)
                self.cursorFirstAction.setEnabled(state2)
            state2 = bool(pltw.dcursor.ic < (pltw.dcursor.X.size) - 1)
            if pltw.xascending:
                 self.cursorRightAction.setEnabled(state2)
                 self.cursorLastAction.setEnabled(state2)
            else:
                self.cursorLeftAction.setEnabled(state2)
                self.cursorLastAction.setEnabled(state2)
            self.cursorUpAction.setEnabled(pltw.activcurv > 0)
            self.cursorDnAction.setEnabled(pltw.activcurv < len(pltw.curvelist)-1)
            self.addMarkAction.setEnabled(True)
            self.clearMarksAction.setEnabled(True)
        else:
            self.cursorLeftAction.setEnabled(False)
            self.cursorFirstAction.setEnabled(False)
            self.cursorRightAction.setEnabled(False)
            self.cursorLastAction.setEnabled(False)
            self.cursorUpAction.setEnabled(False)
            self.cursorDnAction.setEnabled(False)
            self.addMarkAction.setEnabled(False)
            self.clearMarksAction.setEnabled(False)
        self.helpUpdateAction.setEnabled(self.progpath is not None)
        self.windowCascadeAction.setEnabled(self.numpltw > 1)
        self.windowTileAction.setEnabled(self.numpltw > 1)
        self.windowCloseAction.setEnabled(self.numpltw > 0)
        return


    def loadFiles(self):
        """ Load the files which file names are passed as arguments
            when the application is started or file names stored in
            pyDataVis.conf file.

        :return: nothing
        """
        if len(sys.argv) > 1:
            for filename in sys.argv[1:6]: # Load at most 5 files
                if QFileInfo(filename).isFile():
                    self.loadFile(filename)
                    QtWidgets.QApplication.processEvents()
        else:
            settings = QSettings()
            settings.beginGroup("files")
            if settings.contains("lastfile"):
                filename = settings.value("lastfile")
                if QFile.exists(filename):
                     self.loadFile(filename)
                     QtWidgets.QApplication.processEvents()
            settings.endGroup()


    def copyCurrentWinState(self, pltw):
        """ Copy the state of the active plotWin.

            These data are used when the user invokes the 'undo' option
            in the Script menu.

        :param pltw: active plotWin
        :return: nothing
        """
        self.pltwcpy = pltw
        self.datacpy = copy.deepcopy(pltw.blklst)
        self.vectorlistcpy = copy.deepcopy(pltw.vectInfolst)
        self.curvelistcpy = copy.deepcopy(pltw.curvelist)
        self.dirtycpy = pltw.dirty


    def clearCurrentWinState(self):
        """ Clear the data used for the 'undo' 'undo' option in the Script menu.

        :param
        :return: nothing
        """
        self.pltwcpy = None
        self.datacpy = None
        self.vectorlistcpy = None
        self.curvelistcpy = None
        self.dirtycpy = None


#- File menu --------------------------------------------------------------

    def fileNew(self):
        pltw = plotWin(self)
        self.mdi.addSubWindow(pltw)
        self.numpltw += 1
        pltw.show()
        self.updateUI()


    def isAlreadyOpen(self, filename):
        """ Check if the file which name is 'filename' is not already open.

        :param filename: path of the file
        :return: the subwindow if the file is already open, None otherwise.
        """
        for subw in self.mdi.subWindowList():
            pltw = subw.widget()
            if pltw.filename == filename:
                return subw
        return None


    def getCurrentSubWindow(self):
        """ Return the current subwindow.

        :return: the current subwindow or None.
        """
        subw = self.mdi.currentSubWindow()
        if subw is None and self.numpltw > 0:
            # Sometimes QtGui.QMdiArea.currentSubWindow()
            # return None even when there are subwindows.
            wlist = self.mdi.subWindowList(QtWidgets.QMdiArea.StackingOrder)
            if len(wlist) > 0:
                subw = wlist[-1]
        return subw


    def fileOpen(self):
        """ Open a text file.

        :return: nothing
        """
        title = self.app.applicationName() + " -- Open File"
        filter = "Text files (*.txt *.plt);;All files (*.*)"
        dirnam = ""
        subw = self.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            if pltw is not None:
                dirnam = os.path.dirname(pltw.filename)
        else:
            dirnam = self.datapath
        dlg = QtWidgets.QFileDialog(self, title, directory=dirnam, filter=filter)
        filename = dlg.getOpenFileName()[0]
        if filename:
            msg = self.loadFile(filename)
            if msg:
                QtWidgets.QMessageBox.warning(self, title, msg)


    def fileAppend(self):
        """ Append the vector elements contained in a text file to the
            vectors of the active plotWin.

            Call self.appendFile function.

        :return: nothing
        """
        title = self.app.applicationName() + " -- Append a File"
        filter = "Text files (*.txt *.plt);;All files (*.*)"
        errmsg = None
        subw = self.getCurrentSubWindow()
        if subw is None:
            return
        pltw = subw.widget()
        if pltw is not None:
            filename = QtWidgets.QFileDialog.getOpenFileName(self, title,
                                        pltw.filename, filter=filter)[0]
        if filename:
            errmsg = self.appendFile(filename)
        if errmsg is not None:
            msg = "Fail to append {0}: {1}".format(os.path.basename(filename), errmsg)
            QtWidgets.QMessageBox.warning(self, title, msg)



    def loadFile(self, filename):
        """ Load the data from the text file 'filename'

        :param filename: name of the file containing the data.
        :return: a string containing an error message ("" if not error)
        """
        # if the file is already open shows the subwindow
        subw = self.isAlreadyOpen(filename)
        if subw is not None:
            self.mdi.setActiveSubWindow(subw)
            return ""

        # Create a new plot window (plotWin)
        title = self.app.applicationName() + " -- Load Error"
        pltw = plotWin(self, filename)
        err = pltw.load(filename)
        if err == "":
            self.mdi.addSubWindow(pltw)
            pltw.show()
            if not self.test:
                self.raise_()
            self.numpltw += 1
            self.updateUI()
            return ""
        msg = "Failed to load {0}: {1}".format(os.path.basename(filename), err)
        pltw.close()
        del pltw
        return msg


    def appendFile(self, filename):
        """ Append the data in text file 'filename' to the current data.

            Works only if the file contains one data block and the number
            of vectors is the same that the current data block.

        :param filename:
        :return: An errmsg or None if successful.
        """
        title = self.app.applicationName() + " -- Append data from file"
        subw = self.getCurrentSubWindow()
        if subw is None:
            return "No active window"
        pltw = subw.widget()
        if pltw is None:
            return "No data"
        if pltw.blklst is None:
            pltw.load(filename)
            self.mdi.setActiveSubWindow(subw)
            return None

        # Check if the file to append can be decoded.
        errmsg, txt = pltw.fileToString(filename)
        if errmsg:
            return errmsg
        txtlines = txt.splitlines()
        startidx = pltw.findNumData(txtlines)
        if startidx != -1:
            # Try to guess the column separator
            dialect = csv.Sniffer().sniff(txtlines[startidx])
            sep = dialect.delimiter
        else:
            return "Cannot decode the text data"

        errmsg, blocks, headers = textToData(txtlines[startidx:], sep)
        if blocks is None or len(blocks) == 0 or len(blocks[0][0]) == 0:
            errmsg = 'Unable to decode numeric data'
        if blocks is None or not blocks:
            return "No data"
        nb = len(blocks)
        if nb != 1:
            return "The file should contain only one data block"
        (nv2, npt2) = np.shape(blocks[0])
        (nv1, npt1) = np.shape(pltw.blklst[0])
        if nv1 != nv2:
            return "The file should contain the same number of vectors"
        if pltw.blklst[0][0][npt1-1] < pltw.blklst[0][0][0]:
            # X decreasing for initial data
            if blocks[0][0][npt2 - 1] > blocks[0][0][0]:
                 # X increasing for additional data
                 # revert additional data
                 blocks[0] = np.array([x[::-1] for x in blocks[0]])
            # add new data at the beginning
            pltw.blklst[0] = np.concatenate((blocks[0], pltw.blklst[0]), axis=1)
        else:
            # add new data at the end
            pltw.blklst[0] = np.concatenate((pltw.blklst[0], blocks[0]), axis = 1)
        pltw.plotCurves()
        pltw.dirty = True
        # update data table
        if pltw.tabledlg is not None:
            pltw.tabledlg.table.initTable()
        pltw.updatePlot()
        self.updateUI()
        return None


    def fileImport(self):
        """ Import data from a spreadsheet file

        :return: nothing
        """
        title = self.app.applicationName() + " -- Import File"
        filter = "Spreadsheet files (*.xl* *.ods);;All files (*.*)"
        filename = QtWidgets.QFileDialog.getOpenFileName(self, title, filter=filter)[0]
        if not filename:
            return
        err, msg = self.importxls(filename)
        if err:
            QtWidgets.QMessageBox.warning(self, title, msg)


    def importxls(self, filename):
        """ Import data from a spreadsheet file

        :param filename: name of the spreadsheet file to import.
        :return: a tuple (err, msg). err = 0 if success, 1 if failure.
                 msg = "" is no error or contains an error message.
        """
        # Create a new plot window (plotWin)
        ext = os.path.splitext(filename)[1]
        if ext == 'ods':
            try:
                import odfpy
            except ImportError:
                msg = "odfpy  module must be installed to import ODF files"
                return 1, msg
        pltw = plotWin(self, filename)
        msg = pltw.importSheets(filename)
        if msg == "":
            self.mdi.addSubWindow(pltw)
            pltw.show()
            if not self.test:
                self.raise_()
            self.numpltw += 1
            self.updateUI()
            return 0, msg
        msg = "Failed to import {0}: {1}".format(os.path.basename(filename), msg)
        pltw.close()
        del pltw
        return 1, msg


    def fileSave(self):
        """ Save the current data to a file named as pltw.filename.

        :return: True is success, False otherwise.
        """
        title = self.app.applicationName() + " -- Save Error"
        done = False
        subw = self.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            if pltw is not None:
                try:
                    done = pltw.save(pltw.filename)
                except (IOError, OSError) as err:
                    QtWidgets.QMessageBox.warning(self, title,
                          "Failed to save {0}: {1}".format(pltw.filename, err))
                    done = False
        if done:
            msg = "File saved"
            self.statusbar.showMessage(msg, 10000)
        return done


    def fileSaveAs(self):
        """ Save the current data to a file with a new name given by the user.


        :return: True is success, False otherwise.
        """
        title = self.app.applicationName() + " -- Save File As"
        filter = "All files (*.*);;Text files (*.txt *.plt)"
        subw = self.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
        else:
            pltw = None
        done = False
        if pltw is not None:
            basename, ext = os.path.splitext(pltw.filename)
            ext = ext.upper()
            if ext == ".TXT" or ext == ".PLT":
                filename = pltw.filename
            else:
                # the file name is obtained by replacement of the extension by .txt
                filename = "{0}.txt".format(basename)
            filename = QtWidgets.QFileDialog.getSaveFileName(self,
                            title,
                            filename, filter=filter)[0]
            if filename:
                pltw.filename = filename
                done = self.fileSave()
                if done:
                    pltw.setWindowTitle(QFileInfo(filename).fileName())
        return done


    def fileSaveAll(self):
        """ Save the data for every open plotWin.

        :return: nothing
        """
        errors = []
        for subw in self.mdi.subWindowList():
            pltw = subw.widget()
            if pltw.dirty:
                try:
                    pltw.save()
                except (IOError, OSError) as err:
                    errors.append("{0}: {1}".format(pltw.filename, err))
        if errors:
            QtWidgets.QMessageBox.warning(self,
                    "pyDataVis -- Save All Error",
                    "Failed to save\n{0}".format("\n".join(errors)))


    def fileSaveText(self):
        """ Save to a file the text in the Text editor window.

        :return: True on success, False otherwise.
        """
        title = self.app.applicationName() + " -- Save Error"
        subw = self.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
        else:
            pltw = None
        done = False
        if pltw is not None:
            try:
                with open(pltw.filename, "wt") as file:
                    file.write(pltw.datatext.toPlainText())
                done = True
            except (IOError, OSError) as err:
                msg = "Failed to save {0}: {1}".format(str(pltw.filename), err)
                QtWidgets.QMessageBox.warning(self, title, msg)
        if done:
            msg = "Content of text editor saved"
            self.statusbar.showMessage(msg, 10000)
        return done



    def fileExportVeusz(self):
        """ Export to Veusz the vectors in the active plotWin.

            Veusz is a scientific plotting package:
            https://veusz.github.io/

        :return: True on success, False otherwise.
        """
        title = self.app.applicationName() + " -- Export data to Veusz"
        subw = self.getCurrentSubWindow()
        if subw is None:
            return False
        pltw = subw.widget()
        filename = pltw.filename

        # Append .vsz extension
        info = QFileInfo(filename)
        vszname = info.path() + '/' + info.baseName() + ".vsz"
        filename = QtWidgets.QFileDialog.getSaveFileName(self,
                        title,
                        vszname, "Veusz files (*.vsz *.*)")[0]
        if filename:
            vnamlst = []
            for vinfolst in pltw.vectInfolst:
                for vinfo in vinfolst:
                    vnamlst.append(vinfo.name)
            plotlst = pltw.curveToPlotCmd()
            lablst = None
            if pltw.labx is not None:
                lablst = []
                lablst.append(pltw.labx)
                lablst.append(pltw.laby1)
            err, msg = exportToVeusz(str(filename), pltw.blklst, vnamlst, plotlst, lablst)
            if not err:
                msg = "Data exported in {0}".format(os.path.basename(filename))
                self.statusbar.showMessage(msg, 20000)
                return True
            else:
                QtWidgets.QMessageBox.warning(self, title, msg)
                return False


    def fileExportExcel(self):
        """ Export to Excel the vectors in the active plotWin.

        :return: True on success, False otherwise.
        """
        title = self.app.applicationName() + " -- Export data to Excel"
        subw = self.getCurrentSubWindow()
        if subw is None:
            return False
        pltw = subw.widget()
        filename = pltw.filename

        # Append .xlsx extension
        info = QFileInfo(filename)
        xlsname = info.path() + '/' + info.baseName() + ".xlsx"
        filename = QtWidgets.QFileDialog.getSaveFileName(self,
                        title,
                        xlsname, "Excel files (*.xl* *.*)")[0]
        if not filename:
            return False
        err, msg = self.exportExcel(pltw, filename)
        if err:
            QtWidgets.QMessageBox.warning(self, title, msg)
            return False
        self.statusbar.showMessage(msg, 20000)


    def exportExcel(self, pltw, filename):
        """ Export to Excel the vectors in 'pltw'.

        :param pltw: plotWin containing data to export.
        :param filename: name of the spreadsheet file.
        :return: a tuple (err, msg). err = 0 if success, 1 if failure.
                 msg = contains either an error or a success message.
        """
        # Create a pandas dataframe for each data block
        dflst = []
        for i, blk in enumerate(pltw.blklst):
            vnamlst = []
            for vinfo in pltw.vectInfolst[i]:
                vnamlst.append(vinfo.name)
            df = pd.DataFrame(data=np.transpose(pltw.blklst[i]), columns=vnamlst)
            dflst.append(df)
        try:
            # Create an ExcelWriter object
            with pd.ExcelWriter(filename) as writer:
                for i, df in enumerate(dflst):
                    blknam = "Block {0}".format(i + 1)
                    df.to_excel(writer, sheet_name=blknam, index=False)
        except (IOError, OSError) as err:
            return 1, err
        msg = "Data exported in {0}".format(os.path.basename(filename))
        return 0, msg


    def fileExportCSV(self):
        """ Export as CSV the vectors in the active plotWin.

        :return: True on success, False otherwise.
        """
        title = self.app.applicationName() + " -- Export data as CSV"
        subw = self.getCurrentSubWindow()
        if subw is None:
            return False
        pltw = subw.widget()
        filename = pltw.filename

        # Append .csv extension
        info = QFileInfo(filename)
        csvname = "{0}/{1}.csv".format(info.path(), info.baseName())
        filename = QtWidgets.QFileDialog.getSaveFileName(self,
                        title,
                        csvname, "CSV files (*.csv *.*)")[0]
        if not filename:
            return False
        nb = len(pltw.blklst)
        if nb == 1:
            pltw.exportToCSV(0, filename)
        else:
            # Create as many files as block number
            for b in range(nb):
                csvname = filename.replace(".csv", "-{0}.csv".format(b+1))
                if not pltw.exportToCSV(b, csvname):
                    break



    def fileSettings(self):
        """ Change settings.

        :return: nothing
        """
        dlg = settingsDlg(self)
        dlg.exec_()
        return



    def fileUpdateFromText(self):
        """ Update plots & vectors with the content of the Text editor window.

        :return: nothing
        """
        done = self.fileSaveText()
        if done:
            subw = self.getCurrentSubWindow()
            if subw is not None:
                pltw = subw.widget()
                pltw.load(pltw.filename)
                self.updateUI()


    def fileUpdateFromData(self):
        """ Update the content of the Text editor window with the vector elements.

            This function is symmetric of fileUpdateFromText

        :return: nothing
        """
        subw = self.getCurrentSubWindow()
        if subw is not None:
            pltw = subw.widget()
            done = pltw.save(pltw.filename)
            if done:
                pltw.load(pltw.filename)


    def fileViewLogFile(self):
        """ Open the log file and display its content.

        :return: nothing.
        """
        path = os.path.join(self.datapath, "logfile.txt")
        if os.path.isfile(path):
            fo = open(path, 'r')
            txt = fo.read()
            fo.close()
        else:
            txt = ""
        dlg = infoDlg(self, "log")
        dlg.text.setText(txt)
        dlg.exec_()


    # - Curve menu --------------------------------------------------------------

    def selCurvePos(self):
        """ Ask the user to select a curve in the active window self.curvelist.

        :return: A tuple with the active subwindow and the position of the
                 selected curve. Both of these values can be None.
        """
        subw = self.getCurrentSubWindow()
        if subw is None:
            return (None, None)
        pltw = subw.widget()
        if len(pltw.curvelist) == 1:
            # Only one item, no need to choose
            return (pltw, 0)
        # Build the list of curves
        cnamlst = []
        for curv in pltw.curvelist:
            cnamlst.append(curv.name)
        dlg = QtWidgets.QInputDialog()
        item, ok = dlg.getItem(self, "Select the curve",
                               "Curves:", cnamlst, editable=False)
        if ok and item:
            cpos = cnamlst.index(item)
            return (pltw, cpos)
        return (pltw, None)


    def copyCurve(self, cpos, pltw):
        """ Copy in MainWindow global data, the curve 'cpos'.

            Copy the two vectors and their names corresponding to the curve
            having 'cpos' index in the pltw.curvelist.
            This a way to transfer vectors from one plotWin to another.

        :param cpos: index, in pltw.curvelist, of the curve to copy.
        :param pltw: the plotWin containing the curve.
        :return: True if success
        """
        if pltw is None:
            return False
        if cpos < 0 or cpos > len(pltw.curvelist) - 1:
            return False
        xvinfo = pltw.curvelist[cpos].xvinfo
        yvinfo = pltw.curvelist[cpos].yvinfo
        blkno = yvinfo.blkpos
        MainWindow.Xcpy = (pltw.blklst[blkno][xvinfo.vidx]).copy()
        MainWindow.Ycpy = (pltw.blklst[blkno][yvinfo.vidx]).copy()
        MainWindow.labXcpy = xvinfo.name
        MainWindow.labYcpy = yvinfo.name
        return True


    def curvCut(self):
        """ Copy and delete a curve in the active window.

        :return: nothing
            """
        pltw, cpos = self.selCurvePos()
        if cpos is not None:
            if self.copyCurve(cpos, pltw):
                self.copyCurrentWinState(pltw)
                pltw.delCurve(cpos)
                self.updateUI()


    def curvCopy(self):
        """ Copy a curve in the active window.

        :return: nothing.
        """
        pltw, cpos = self.selCurvePos()
        if cpos is not None:
            if self.copyCurve(cpos, pltw):
                cname = pltw.curvelist[cpos].name
                msg = "Curve {0} was copied in memory".format(cname)
                self.statusbar.showMessage(msg, 10000)
                self.updateUI()


    def curvDuplicate(self):
        """ Duplicate a curve in the active window.

        :return: nothing.
        """
        pltw, cpos = self.selCurvePos()
        if cpos is not None:
            self.copyCurrentWinState(pltw)
            pltw.duplicateCurve(cpos)


    def curvSaveInFile(self):
        """ Save a curve (X,Y vectors) to a file.

        :return: nothing.
        """
        pltw, cpos = self.selCurvePos()
        if cpos is not None:
            filter = "Text files (*.txt *.*)"
            title = self.app.applicationName() + " -- Save a curve in a file"
            filename = QtWidgets.QFileDialog.getSaveFileName(self,
                                                             title,
                                                             pltw.filename,
                                                             filter)[0]
            if filename:
                if pltw.saveCurveInFile(cpos, filename):
                    cname = pltw.curvelist[cpos].name
                    msg = "Curve {0} was saved in file".format(cname)
                    self.statusbar.showMessage(msg, 10000)


    def curvPaste(self):
        """ Paste a curve in the active window.

            Paste the the curve previously copied in MainWindow global data.

        :return: nothing.
        """
        if MainWindow.Ycpy is not None:
            subw = self.getCurrentSubWindow()
            if subw is not None:
                pltw = subw.widget()
                self.copyCurrentWinState(pltw)
                if pltw.pasteCurve(MainWindow.Xcpy, MainWindow.labXcpy,
                                   MainWindow.Ycpy, MainWindow.labYcpy):
                    self.updateUI()


    def curvDelete(self):
        """ Delete a curve in the active window.

        :return: nothing.
        """
        pltw, cpos = self.selCurvePos()
        if cpos is not None:
            self.copyCurrentWinState(pltw)
            if pltw.delCurve(cpos):
                self.updateUI()


    # - Marks & Cursor menu --------------------------------------------------------------

    def cursorUp(self):
        """ Move the data cursor to the previous curve in the active window.

        :return: nothing
        """
        subw = self.getCurrentSubWindow()
        if subw is None:
            return
        pltw = subw.widget()
        if pltw.dcursor == None:
            return
        if pltw.activcurv > 0:
            pltw.activcurv -= 1
        pltw.dcursor.updateCurve()
        pltw.dcursor.updateLinePos()
        # update data table
        if pltw.tabledlg is not None:
            pltw.tabledlg.table.initTable()
        self.updateUI()


    def cursorDn(self):
        """ Move the data cursor to the next curve in the active window.

        :return: nothing
        """
        subw = self.getCurrentSubWindow()
        if subw is None:
            return
        pltw = subw.widget()
        if pltw.dcursor is None:
            return
        if pltw.activcurv < len(pltw.curvelist) - 1:
            pltw.activcurv += 1
        pltw.dcursor.updateCurve()
        pltw.dcursor.updateLinePos()
        if pltw.tabledlg is not None:
            pltw.tabledlg.table.initTable()
        self.updateUI()


    def cursorLeft(self):
        """ Move the data cursor to the previous data point of the active curve.

        :return: nothing
         """
        subw = self.getCurrentSubWindow()
        if subw is None:
            return
        pltw = subw.widget()
        if pltw.dcursor == None:
            return
        npt = pltw.dcursor.X.size
        if pltw.dcursor.X[npt - 1] > pltw.dcursor.X[0]:
            if pltw.dcursor.ic > 0:
                pltw.dcursor.move(None, pltw.dcursor.ic - 1)
        else:
            if pltw.dcursor.ic < npt - 1:
                pltw.dcursor.move(None, pltw.dcursor.ic + 1)
        # update data table
        if pltw.tabledlg is not None:
            pltw.tabledlg.table.setCurrentPos(pltw.dcursor.ic)
        self.updateUI()


    def cursorRight(self):
        """ Move the data cursor to the next data point of the active curve.

        :return: nothing
        """
        subw = self.getCurrentSubWindow()
        if subw is None:
            return
        pltw = subw.widget()
        if pltw.dcursor == None:
            return
        npt = pltw.dcursor.X.size
        if pltw.dcursor.X[npt - 1] > pltw.dcursor.X[0]:
            # ascending order
            if pltw.dcursor.ic < npt - 1:
                pltw.dcursor.move(None, pltw.dcursor.ic + 1)
        else:
            if pltw.dcursor.ic > 0:
                pltw.dcursor.move(None, pltw.dcursor.ic - 1)

        # update data table
        if pltw.tabledlg is not None:
            pltw.tabledlg.table.setCurrentPos(pltw.dcursor.ic)
        self.updateUI()


    def cursorFirst(self):
        """ Move the data cursor to the first data point of the active curve.

        :return: nothing
        """
        subw = self.getCurrentSubWindow()
        if subw is None:
            return
        pltw = subw.widget()
        if pltw.dcursor == None:
            return
        pltw.dcursor.move(None, 0)
        # update data table
        if pltw.tabledlg is not None:
            pltw.tabledlg.table.setCurrentPos(pltw.dcursor.ic)
        self.updateUI()


    def cursorLast(self):
        """ Move the data cursor to the last data point of the active curve.

        :return: nothing
        """
        subw = self.getCurrentSubWindow()
        if subw is None:
            return
        pltw = subw.widget()
        if pltw.dcursor == None:
            return
        npt = pltw.dcursor.X.size
        pltw.dcursor.move(None, npt - 1)
        # update data table
        if pltw.tabledlg is not None:
            pltw.tabledlg.table.setCurrentPos(pltw.dcursor.ic)
        self.updateUI()


    def addMark(self):
        """ Put a marker at the cursor position (if any).

            Update the plot

        :return: noting.
        """
        subw = self.getCurrentSubWindow()
        if subw is None:
            return
        pltw = subw.widget()
        if pltw.dcursor == None:    # cursor pos not defined
            return
        if len(pltw.markList) < 2:
            marker = dCursor(pltw, 'V')
            pltw.markList.append(marker)
            marker.setIndex(pltw.dcursor.getIndex())
        else:
            cursIdx = pltw.dcursor.getIndex()
            m1Idx = pltw.markList[1].getIndex()
            pltw.markList[1].setIndex(cursIdx)
            pltw.markList[0].setIndex(m1Idx)
        self.updateUI()



    def clearMarks(self):
        """ Remove all the markers and the data cursor in the active window.

        :return: nothing.
        """
        subw = self.getCurrentSubWindow()
        if subw is None:
            return
        pltw = subw.widget()
        if pltw.dcursor == None:
            return
        pltw.clearMarks()



    # - Convert menu --------------------------------------------------------------

    def convert(self, sel):
        """ Router for conversion functions.
            Call convSelector in convert.py module.

        :param sel:
        :return: nothing
        """
        sender = self.sender()
        sel = sender.text()
        subw = self.getCurrentSubWindow()
        if subw is None:
            return
        pltw = subw.widget()
        text = str(pltw.datatext.toPlainText()).rstrip('\r\n')
        lines = text.split('\n')
        err, msg, savename = convSelector(self, sel, lines, pltw.filename)
        if not err and msg is not None:
            pltw.info.setText(msg)
            if savename is not None:
                # load the converted file
                msg = self.loadFile(savename)
                if msg:
                    title = "{0} conversion".format(sel)
                    QtWidgets.QMessageBox.warning(self, title, msg)
                else:
                    # Close the previous SubWindow if the file was overwritten
                    if sel != "CIF":
                        subw.close()


    # - Script menu --------------------------------------------------------------

    def loadScript(self):
        """ Load a script file in the Script window.

        :return: nothing
        """
        subw = self.getCurrentSubWindow()
        if subw is None:
            return
        pltw = subw.widget()
        title = "Open a script file"
        filter = "Text files (*.txt);;All files (*.*)"
        dir = os.path.join(self.datapath, "scripts")
        filename = QtWidgets.QFileDialog.getOpenFileName(self, title, dir, filter)[0]
        if filename:
            with open(filename) as file:
                pltw.scriptwin.setPlainText(file.read())


    def saveScript(self):
        """ Save to a file the text in the Script window.

        :return: nothing
        """
        subw = self.getCurrentSubWindow()
        if subw is None:
            return
        pltw = subw.widget()
        title = "Save a script file"
        filter = "Text files (*.txt);;All files (*.*)"
        dir = os.path.join(self.datapath, "scripts")
        if not os.path.exists(dir):
            # the scripts folder does not exist, create it
            os.makedirs(dir)
        filename = QtWidgets.QFileDialog.getSaveFileName(self, title, dir, filter)[0]
        if filename:
            with open(filename, "wt") as file:
                file.write(pltw.scriptwin.toPlainText())



    def runScript(self):
        """ Execute the script commands in the Script window.

        :return: nothing.
        """
        title = "Executing a command"
        subw = self.getCurrentSubWindow()
        if subw is None:
            return
        pltw = subw.widget()
        cmd = pltw.scriptwin.toPlainText()
        if not cmd:
            msg = "Nothing to execute !"
            QtWidgets.QMessageBox.warning(self, title, msg)
            return
        self.copyCurrentWinState(pltw)
        err = 0
        msg = ""
        cmd = str(cmd)
        plotlist = []
        for l, line in enumerate(cmd.splitlines()):
            line = line.strip()
            if line and not line.startswith('#'):
                if line.startswith('plot') or line.startswith('lab') or \
                        line.startswith('text') or line.startswith('arrow') or \
                        line.startswith('symbol') or line.startswith('nosymbol'):
                    msg = pltw.checkPlotCmd(line, pltw.curvelist)
                    if not msg:
                        plotlist.append(line)
                        msg = pltw.checkPlotOrder(plotlist)
                    if msg:
                        err = 1
                else:
                    scrpt = script(pltw)
                    (err, msg) = scrpt.dispatch(line)
            if err > 0:
                break
        if err > 0:
            msg = "Error in line {0}, {1}".format(l + 1, msg)
            QtWidgets.QMessageBox.warning(self, title, msg)
        if err <= 0:
            if msg:
                dlg = infoDlg(self, "info")
                dlg.text.setText(msg)
                dlg.exec_()
                err = 0
        if err == 0:
            if plotlist:
                pltw.scriptPlot(plotlist)
            else:
                pltw.updatePlot()
                if pltw.dcursor is not None:
                    pltw.dcursor.updateLinePos()
                    # update data table
            if pltw.tabledlg is not None:
                pltw.tabledlg.table.initTable()
            self.updateUI()



    def runPyScript(self):
        """ Execute a Python script

            The Python script is in the Script window of the active window.
            The script is first saved in a file with the filename
            'scriptfile.py' and then executed with the subprocess.call command.

        :return: nothing.
        """
        subw = self.getCurrentSubWindow()
        if subw is None:
            return
        pltw = subw.widget()

        cmd = pltw.scriptwin.toPlainText()
        if not cmd:
            msg = "Nothing to execute !"
            QtWidgets.QMessageBox.warning(self, "Execute a command", msg)
            return
        path= os.path.join(self.datapath, "input.txt")
        if os.path.isfile(path):
            # delete input.txt file
            os.remove(path)
        if pltw.curvelist != []:
            # Save the active curve in input.txt
            pltw.saveCurveInFile(pltw.activcurv, path)
        # Add imports
        pyscript = "import numpy as np\n"
        if os.path.isfile(path):
            # Load active curve from input.txt
            path = "\"{0}\"".format(path)
            pyscript += "A = np.loadtxt({0}, unpack=True)\n".format(path)
            pyscript += "X=A[0]\nY=A[1]\n"
        # Add the script from Script window
        pyscript += cmd
        # Save the script in 'scripts/scriptfile.py'
        path = os.path.join(self.datapath, "scripts")
        if not os.path.exists(path):
            # the scripts folder does not exist, create it
            os.makedirs(path)
        scriptpath = os.path.join(path, "scriptfile.py")
        with open(scriptpath, "wt") as file:
             file.write(pyscript)
        # execute the script, the output is stored in "output.txt" file.
        import subprocess
        path = os.path.join(self.datapath, "output.txt")
        with open(path, "w+") as output:
            subprocess.run(["python", scriptpath], stdout=output)
        # Show the process output in info window
        with open(path) as file:
            pltw.info.setPlainText(file.read())



    def clearScript(self):
        """ Clear the Script window.

        :return: nothing.
        """
        subw = self.getCurrentSubWindow()
        if subw is None:
            return
        pltw = subw.widget()
        pltw.scriptwin.clear()
        pltw.scriptwin.setFocus()
        pltw.displayInfo()



    def undoLast(self):
        """ Return to the state preceding the last command.

        :return: nothing.
        """
        if self.pltwcpy is None:
            return
        for subw in self.mdi.subWindowList():
            pltw = subw.widget()
            if pltw == self.pltwcpy:
                pltw.blklst = self.datacpy
                pltw.vectInfolst = self.vectorlistcpy
                pltw.curvelist = self.curvelistcpy
                pltw.dirty = self.dirtycpy
                pltw.updatePlot()
                self.updateUI()
                break



    # - Tools menu --------------------------------------------------------------

    def smoothTool(self, pltw=None, cpos=None):
        """ Launch the interactive Smoothing tool.

            If pltw and cpos parameters are not passed they are being
            requested from the user.
        :param pltw: plotWin containing data
        :param cpos: position of the curve in pltw.curvelist
        :return: nothing
        """
        if cpos is None:
            pltw, cpos = self.selCurvePos()
        if cpos is not None and pltw is not None:
            if self.smoothDlg is None:
                self.smoothDlg = smoothDlg(self, pltw, cpos)
            else:
                self.smoothDlg.initDlg(cpos)
            self.smoothDlg.setModal(True)
            self.smoothDlg.show()


    def splinSmoothTool(self, pltw=None, cpos=None):
        """ Launch the interactive Spline Smoothing Tool.

            If pltw and cpos parameters are not passed they are being
            requested from the user.
        :param pltw: plotWin containing data
        :param cpos: position of the curve in pltw.curvelist

        :return: nothing.
        """
        if cpos is None:
            pltw, cpos = self.selCurvePos()
        if cpos is not None and pltw is not None:
            if self.splinSmoothDlg is None:
                self.splinSmoothDlg = splinSmoothDlg(self, pltw, cpos)
            else:
                self.splinSmoothDlg.initDlg(cpos)
            self.splinSmoothDlg.setModal(True)
            self.splinSmoothDlg.show()


    def ALS_SmoothTool(self, pltw=None, cpos=None):
        """ Launch the interactive Asymetric Least Squares Smoothing tool.

            If pltw and cpos parameters are not passed they are being
            requested from the user.
        :param pltw: plotWin containing data
        :param cpos: position of the curve in pltw.curvelist

        :return: nothing.
        """
        if cpos is None:
            pltw, cpos = self.selCurvePos()
        if cpos is not None and pltw is not None:
            ALS_Smoothdlg = ALS_SmoothDlg(self, pltw, cpos)
            ALS_Smoothdlg.setModal(True)
            ALS_Smoothdlg.show()


    def fitCurveTool(self, pltw=None, cpos=None, modelno=None):
        """ Launch the interactive Fitting tool.

            If pltw and cpos parameters are not passed they are being
            requested from the user.
        :param pltw: plotWin containing data
        :param cpos: position of the curve in pltw.curvelist
        :return: nothing.
        """
        if cpos is None:
            subw = self.getCurrentSubWindow()
            if subw is not None:
                pltw = subw.widget()
                dlg = modelSelectDlg(self, pltw)
                # Init widgets
                dlg.nameComboBox.setCurrentIndex(pltw.activcurv)
                dlg.modelComboBox.setCurrentIndex(self.fitmodel)
                if dlg.exec_():
                    self.copyCurrentWinState(pltw)
                    cpos, modelno = dlg.getValues()
        if cpos is not None and modelno is not None:
            fitdlg = fitCurveDlg(self, pltw, cpos, modelno)
            fitdlg.setModal(True)
            fitdlg.show()



    def findPkTool(self, pltw=None, cpos=None):
        """ Launch the Peak Finding tool.

            If pltw and cpos parameters are not passed they are being
            requested from the user.
        :param pltw: plotWin containing data
        :param cpos: position of the curve in pltw.curvelist
        :return: nothing.
        """
        if cpos is None:
            pltw, cpos = self.selCurvePos()
        if cpos is None:
            return
        pkFinddlg = pkFindDlg(self, pltw, cpos)
        pkFinddlg.setModal(True)
        ret = pkFinddlg.exec()
        if ret:
            peakindx = pkFinddlg.peakindx
            mpw = pkFinddlg.mpw
        else:
            return
        blkno = pltw.curvelist[cpos].xvinfo.blkpos
        xpos = pltw.curvelist[cpos].xvinfo.vidx
        ypos = pltw.curvelist[cpos].yvinfo.vidx
        X = pltw.blklst[blkno][xpos]
        Y = pltw.blklst[blkno][ypos]
        # Convert results in guess for pkfitDlg (typ, pos, amp, FWHM)
        guess = ""
        npk = len(peakindx)
        for idx in peakindx:
            pos = X[idx]
            amp = round_to_n(Y[idx] * 0.8, 3)
            stpk = "G,{0},{1},{2}".format(pos, amp, mpw)
            if idx != peakindx[npk - 1]:
                 # add the separator for the next peak
                stpk += ','
            guess += stpk
        self.copyCurrentWinState(pltw)
        pkfitdlg = pkFitDlg(self, pltw, cpos, guess)
        pkfitdlg.setModal(True)
        pkfitdlg.show()



    def fitPkTool(self, pltw=None, cpos=None, guess=None):
        """ Launch the interactive Peak Fitting tool.

            If pltw and cpos parameters are not passed they are being
            requested from the user.
        :param pltw: plotWin containing data
        :param cpos: position of the curve in pltw.curvelist
        :param guess: string containing the first estimate of the
                      peak parameters.
        :return: nothing.
        """
        if cpos is None:
            pltw, cpos = self.selCurvePos()
        if cpos is None:
            return
        self.copyCurrentWinState(pltw)
        pkfitdlg = pkFitDlg(self, pltw, cpos, guess)
        if pkfitdlg.stguess is None:
            del pkfitdlg
        else:
            pkfitdlg.setModal(True)
            pkfitdlg.show()



    def interpolTool(self):
        """ Launch the interactive Interpolation tool.

            Work on all the vectors of a data block.

        :return: nothing
        """
        subw = self.getCurrentSubWindow()
        if subw is None:
            return
        pltw = subw.widget()
        # initialize parameters with active curve parameters
        curvinfo = pltw.curvelist[pltw.activcurv]
        xnam = curvinfo.xvinfo.name
        blkno = curvinfo.xvinfo.blkpos
        xpos = curvinfo.xvinfo.vidx
        # Check duplicates
        u, c = np.unique(pltw.blklst[blkno][xpos], return_counts=True)
        dup = u[c > 1]
        if dup.size > 0:
            msg = "There are duplicates in: {0}\n".format(xnam)
            msg += "They must be removed before doing interpolation.\n"
            msg += "You can use the script command delmultx {0}".format(xnam)
            QtWidgets.QMessageBox.warning(self, "Interpolation", msg)
            return
        xmin = (pltw.blklst[blkno][xpos]).min()
        xmax = (pltw.blklst[blkno][xpos]).max()
        xspan = xmax - xmin
        dx = xspan / (len(pltw.blklst[blkno][xpos]) - 1)
        parmlist = [ ["Data block", blkno], ["dx", dx], ["s", 0], ["k", 3] ]
        interpoldlg = interpolDlg(self, pltw, parmlist)
        self.copyCurrentWinState(pltw)
        interpoldlg.setModal(True)
        interpoldlg.show()



    def baselineTool(self, pltw=None, cpos=None):
        """ Launch the interactive Baseline correction tool.

            If pltw and cpos parameters are not passed they are being
            requested from the user.
        :param pltw: plotWin containing data
        :param cpos: position of the curve in pltw.curvelist
        :return: nothing.
        """
        if cpos is None:
            pltw, cpos = self.selCurvePos()
        if cpos is not None:
            baselinedlg = baselineDlg(self, pltw, cpos)
            baselinedlg.setModal(True)
            baselinedlg.show()


    def noiseTool(self, pltw=None, cpos=None):
        """ Launch the interactive Add noise tool.

            If pltw and cpos parameters are not passed they are being
            requested from the user.
        :param pltw: plotWin containing data
        :param cpos: position of the curve in pltw.curvelist
        :return: nothing
        """
        if cpos is None:
            pltw, cpos = self.selCurvePos()
        if cpos is not None:
            noisedlg = noiseDlg(self, pltw, cpos)
            noisedlg.setModal(True)
            noisedlg.show()


    def deNoiseTool(self, pltw=None, cpos=None):
        """ Launch the Remove noise tool.

            If pltw and cpos parameters are not passed they are being
            requested from the user.
        :param pltw: plotWin containing data
        :param cpos: position of the curve in pltw.curvelist
        :return: nothing.
        """
        if cpos is None:
            pltw, cpos = self.selCurvePos()
        if cpos is not None:
            denoisedlg = deNoiseDlg(self, pltw, cpos)
            denoisedlg.setModal(True)
            denoisedlg.show()



    def tableTool(self):
        """ Show the data table.

        :return: nothing
        """
        subw = self.getCurrentSubWindow()
        if subw is None:
            return
        pltw = subw.widget()
        if pltw.tabledlg is None:
            pltw.tabledlg = tableDlg(pltw)
        if pltw.tabledlg is not None and pltw.curvelist:
            pltw.tabledlg.show()


    #- Help menu --------------------------------------------------------------

    def help(self):
        """ Open the pyDataVis manual in the Web Browser.

        :return: nothing.
        """
        import webbrowser
        url = 'https://pydatavis.github.io/pyDataVis.html'
        if platform.system() == "Darwin":
            webbrowser._browsers['safari'][1].open(url)
        else:
            webbrowser.open(url)



    def getDataFromUrl(self, url):
        """  Copy data from 'url' in 'self.datapath' folder

        :param url: the GitHub URL.
        :return: an error message (= "" if no error)
        """
        self.app.setOverrideCursor(Qt.WaitCursor)
        self.statusbar.showMessage("Cloning pyDataVis data from GitHub")
        # Clone url
        msg = getDataFromUrl(url, self.datapath)
        self.statusbar.showMessage("")
        self.app.restoreOverrideCursor()
        return msg


    def updateFromGitHub(self):
        """ Update from GitHub

        :return: True is success.
        """
        title = "Update from GitHub"
        msg = ""
        scriptpath = os.path.join(self.datapath, "scripts")
        tmppath = os.path.join(self.datapath, "tmp")
        tmpscriptpath = os.path.join(tmppath, "scripts")
        if os.path.exists(scriptpath):
            # Save scripts folder in temporary folder
            if os.path.exists(tmppath):
                shutil.rmtree(tmppath)
            os.makedirs(tmppath)
            msg = copyFiles(scriptpath, tmpscriptpath)
        if not msg:
            dirlst = os.listdir(self.datapath)
            files = [f for f in dirlst if f != 'tmp']
            # Delete all files and folders in self.datapath but the tmp folder
            try:
                for f in files:
                    path = os.path.join(self.datapath, f)
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
            except IOError as err:
                msg = "Fail to delete {0}: {1}".format(f, err)
        if not msg:
            url = "https://github.com/pyDataVis/pyDataVis/archive/main.zip"
            msg = self.getDataFromUrl(url)
        if not msg:
            # Restore 'scripts' folder from tmp folder
            if os.path.exists(tmpscriptpath):
                msg = copyFiles(tmpscriptpath, scriptpath)
        if msg:
            QtWidgets.QMessageBox.warning(self, title, msg)
            return False
        return True


    def latestVersion(self):
        """ Get latest version of pyDataVis from website.

        :return: a string with the version number or None if error.
        """
        url = 'https://raw.githubusercontent.com/pyDataVis/pyDataVis/main/VERSION'
        try:
            with urlopen(url) as f:
                p = f.read()
            latest = p.decode('ascii').strip()
        except Exception:
            return None
        return latest


    def checkUpdate(self):
        """ Check if there is a new version on GitHub

        :return: True if a new version exists.
        """
        curver = self.latestVersion()
        if curver == None or curver <= __version__:
            return False

        title = "Update pyDataVis"
        msg = "There is a new version of pyDataVis, do you want to update ?"
        r = QtWidgets.QMessageBox.information(self, title, msg,
                     QtWidgets.QMessageBox.Yes |
                     QtWidgets.QMessageBox.No)
        if r != QtWidgets.QMessageBox.Yes:
            return
        if not self.updateFromGitHub():
            return

        if self.progpath is not None and os.access(self.progpath, os.W_OK):
            msg = "Ok to quit pyDataVis ?"
            ret = QtWidgets.QMessageBox.question(self, title, msg,
                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if ret == QtWidgets.QMessageBox.Yes:
                msg = copyFiles(self.datapath, self.progpath)
                if not msg:
                    sys.exit(0)
                    # Restart
                    # os.execv(['python', __file__] + sys.argv[1:])



    def runSelfTests(self, sel):
        """ Run self tests, mainly on script commands.

        :return: nothing
        """
        if not os.path.exists(self.testspath):
            # Try to load data files from GitHub
            url = "https://github.com/pyDataVis/pyDataVis.git"
            clonedir = os.path.join(self.datapath, "tmp", "pyDataVis")
            errmsg = self.getDataFromUrl(clonedir, url)
            if errmsg:
                title = "Fail to get tests data from GitHub"
                QtWidgets.QMessageBox.warning(self, title, errmsg)
        if os.path.exists(self.testspath):
            sender = self.sender()
            sel = sender.text()
            self.test = True
            if sel == "Run all tests":
                runAllTests(self)
            else:
                runTests(self, sel)
            self.test = False



    def helpAbout(self):
        """ Open About dialog.

        :return: nothing.
        """
        txt = "pyDataVis is an open source application for interactive\n" \
              "visualization, analysis and manipulation of scientific\n" \
              "data.\npyDataVis is written in Python 3. It uses PyQt5 as\n" \
              "graphic user interface (GUI) and Matplotlib for plotting.\n\n" \
              "Author: Pierre Alphonse\n\n"
        txt += "Version: {0}\n\n".format(__version__)
        txt += "MIT License"
        dlg = infoDlg(self, "about")
        dlg.text.setText(txt)
        dlg.exec_()


#- Window menu --------------------------------------------------------------

    def updateWindowMenu(self):
        self.windowMenu.clear()
        self.addActions(self.windowMenu, (self.windowCascadeAction,
                self.windowTileAction, None,
                self.windowCloseAction))
        subwlst = self.mdi.subWindowList()
        if not subwlst:
            return
        self.windowMenu.addSeparator()
        i = 1
        menu = self.windowMenu
        for subw in subwlst:
            title = subw.windowTitle()
            if i == 10:
                self.windowMenu.addSeparator()
                menu = menu.addMenu("&More")
            accel = ""
            if i < 10:
                accel = "&{0} ".format(i)
            elif i < 36:
                accel = "&{0} ".format(chr(i + ord("@") - 9))
            action = menu.addAction("{0}{1}".format(accel, title))
            action.triggered.connect(self.windowMapper.map)
            self.windowMapper.setMapping(action, subw)
            i += 1


