"""  pyDataVis window module
"""
import os, csv

from PyQt5.QtCore import (QFileInfo, QSize, Qt)
from PyQt5 import QtWidgets

import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.pyplot import Arrow
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)


from utils import (isNumber, isNumeric, isNumData)
from utils import (textToData, dataToFile, JcampDX, arrayToString)


# - vector class ------------------------------------------------------------

class vectInfo(object):
    """ vectInfo is used to store information about a data vector
    """
    def __init__(self, blkpos, vidx, name):
        self.blkpos = blkpos       # index of array whose vector belongs to
        self.vidx = vidx           # index of vector in the array
        self.name = name           # vector name

    def makecopy(self):
        newVect = vectInfo(self.blkpos, self.vidx, self.name)
        return newVect

# - curveData class ------------------------------------------------------------

class curveInfo(object):
    """ curveInfo' is used to store information about a curve
    """
    def __init__(self, name="", xvinfo=None, yvinfo=None):
        self.name = name             # curve name
        self.xvinfo = xvinfo         # vector X
        self.yvinfo = yvinfo         # vector Y
        self.axis = 1
        self.plottyp = None          # type of plot ('line', 'scat', 'bar')


# - dcursor class ------------------------------------------------------------

class dCursor:
    """  dCursor handles data marker functions (data cursor and markers).

        If typ == 'H' the marker is an horizontal line
        If typ == 'V' the marker is a vertical line
        if typ == '+' the marker is the intersection of an horizontal and
        vertical line
    """
    def __init__(self, parent, typ='+'):
        self.parent = parent
        self.typ = typ
        self.colour = 'gray'
        if typ == 'H':
            self.hl = parent.axes.axhline(color=self.colour)  # the horiz line
        elif typ == 'V':
            self.vl = parent.axes.axvline(color=self.colour)  # the vert line
        else:
            self.typ = '+'
            self.colour = 'chocolate'
            self.hl = parent.axes.axhline(color=self.colour)  # the horiz line
            self.vl = parent.axes.axvline(color=self.colour)  # the vert line
        self.hl2 = None
        self.blkno = 0           # data block of the active curve
        self.xpos = 0            # index of X data of the active curve
        self.ypos = 1            # index of Y data of the active curve
        self.X = None            # X data of the active curve
        self.Y = None            # Y data of the active curve
        self.xc = None           # x coordinate of the dcursor
        self.yc = None           # y coordinate of the dcursor
        self.ic = 0              # index of the dcursor
        self.updateCurve()


    def updateCurve(self):
        """ Update the dCursor data when the activcurv is changed

        :return: nothing
        """
        cinfo = self.parent.curvelist[self.parent.activcurv]
        self.X = self.parent.blklst[cinfo.xvinfo.blkpos][cinfo.xvinfo.vidx]
        self.Y = self.parent.blklst[cinfo.yvinfo.blkpos][cinfo.yvinfo.vidx]
        npt = self.X.size
        self.parent.xascending = (self.X[npt-1] > self.X[0])
        self.blkno = cinfo.yvinfo.blkpos
        if self.xc is None:
            self.ic = 0
        else:
            self.ic = self.parent.xToIdx(self.xc, self.blkno, self.xpos)
        if self.ic is not None:
            if self.ic >= npt:
                self.ic = npt-1
        if self.parent.curvelist[self.parent.activcurv].axis == 1:
            self.lh2 = None
        else:
            if self.parent.y2axis is not None:
                self.hl2 = self.parent.y2axis.axhline(color=self.colour)


    def updateLinePos(self, redraw=False):
        """ Update the cursor position from self.X, self.Y et self.indx

        :param redraw: if True redraw everything, if False update only
               the lines.
        :return: nothing
        """
        self.xc = self.X[self.ic]
        self.yc = self.Y[self.ic]
        if redraw:
            self.parent.plotCurves()
        else:
            if self.typ == 'V' or self.typ == '+':
                self.vl.set_xdata(self.xc)
            if self.typ == 'H' or self.typ == '+':
                if self.parent.curvelist[self.parent.activcurv].axis == 1:
                    self.hl.set_ydata(self.yc)
                else:
                    self.hl2.set_ydata(self.yc)
            self.parent.canvas.draw()
        # update status line with the cursor position
        msg = "{0}: no: {1:d}, xc = {2:g}, yc = {3:g}".\
            format(self.parent.curvelist[self.parent.activcurv].name,
                   self.ic+1, self.xc, self.yc)
        self.parent.parent.statusbar.showMessage(msg)


    def setIndex(self, index):
        """ Move the cursor position to 'index'

        :param index: int giving the new data index
        :return: nothing
        """
        if index >= 0 and index < len(self.parent.blklst[self.blkno][self.xpos]):
            self.ic = index
            self.updateLinePos()


    def getIndex(self):
        """ Return the index position of the Cursor

        :return: the index
        """
        return self.ic


    def getxy(self):
        """  Return the coordinates of the Cursor

        :return: a tuple containing
        """
        return (self.xc, self.yc)



    def move(self, event=None, indx=None):
        """ Move the Cursor to a new index position.

        :param event: mouse event.
        :param indx: data index of the place to move.
        :return: nothing.
        """
        if indx is None and event is None:
            return
        if indx is None:
            x, y = event.xdata, event.ydata
            if not self.parent.xascending:
               Xr = self.X[::-1]
               indx = self.X.size - np.searchsorted(Xr, x) - 1
            else:
               indx = np.searchsorted(self.X, x)
        if indx < 0:
            indx = 0
        elif indx >= len(self.parent.blklst[self.blkno][self.xpos]):
            indx = len(self.parent.blklst[self.blkno][self.xpos])
        self.setIndex(indx)


# - Line class ------------------------------------------------------------

class lineSeg:
    """ Create a line segment marker

    """
    def __init__(self, x1, y1, x2, y2, color):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.color = color


# - plotWin class ------------------------------------------------------------

class plotWin(QtWidgets.QDialog):
    newcpt = 1        # Global counter for the numbering of new plotWin objects

    def __init__(self, parent=None, filename=None):
        """ Plotting area and Text window.

        :param parent: pyDataVis MainWindow
        :param filename: name of the file which stores the data.
        """
        super(plotWin, self).__init__(parent)

        self.colors = ('blue','red','green','gray','magenta','black','brown',
                       'cyan', 'cadetblue', 'chocolate', 'coral', 'darkred',
                       'burlywood', 'darkgreen', 'darkblue', 'darkcyan',
                       'yellow', 'aqua', 'aquamarine', 'blueviolet',
                       'cornflowerblue', 'crimson', 'darkgoldenrod',
                       'darkkhaki', 'darkmagenta', 'darkolivegreen',
                       'darkorange', 'darksalmon', 'darkseagreen',
                       'darkslateblue', 'darkslategray', 'darkviolet',
                       'deeppink', 'goldenrod','greenyellow', 'hotpink',
                       'indigo', 'white')
        self.filext = ('TXT', 'DAT', 'ASC', 'CSV', 'JDX', 'PLT', 'PRF' )
        self.parent = parent
        if filename is None:
            while True:
                filename = str("Unnamed-{0}.txt".format(plotWin.newcpt))
                if self.parent.isAlreadyOpen(filename):
                    plotWin.newcpt += 1
                else:
                    break
            plotWin.newcpt += 1
        self.filename = filename
        self.dirty = False
        self.vectInfolst = []   # list of list of vectInfo object
        self.curvelist = []     # List of curves (curveInfo object)
        self.blklst = None      # List of numpy array containing the data blocks
        self.nvect = 0          # number of vectors
        self.nelem = 0          # number of elements in each vector
        self.headers = None     # list of list lines storing file header
        self.axes = None        # matplotlib.axes.Axes object
        self.y2axis = None      # matplotlib.axes.Axes object
        self.labx = None        # legend of X axis
        self.laby1 = None       # legend of Y1 axis
        self.laby2 = None       # legend of Y2 axis
        self.arrows = []        # parameters for drawing arrows on plot
        self.plottext = []      # parameters for writing text label on plot
        self.invertX = False
        self.invertY = False
        self.logX = False
        self.logY = False
        self.dplot = []         # table of Line2D object
        self.legend = None
        self.dcursor = None     # data reader (dCursor type)
        self.markList = []      # list of data Markers (dCursor type)
        self.lineList = []      # list of line segment Markers (LinSeg type)
        self.activcurv = 0      # index of the curve followed by the dcursor
        self.tabledlg = None    # data Table (tableDlg object)

        # Try to adapt the window size to screen resolution
        ww = self.parent.scrsize.width()
        if ww > 1920:
            figdpi = 110
            w = 8.0
            h = 6.0
        else:
            figdpi = 70
            w = 7.0
            h = 6.0
        self.fig = Figure((w, h), dpi=figdpi)

        # self.canvas is the "Plotting area"
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.canvas.setFocusPolicy(Qt.StrongFocus)
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        if ww > 1920:
            self.mpl_toolbar.setIconSize(QSize(25, 25))
        else:
            self.mpl_toolbar.setIconSize(QSize(15, 15))
        # self.datatext is the "Text editor window"
        self.datatext = QtWidgets.QTextEdit(self)

        # self.scriptwin is the "Script window"
        self.scriptwin = QtWidgets.QTextEdit(self)
        # self.info is the "Information window"
        self.info = QtWidgets.QTextEdit(self)
        self.info.setReadOnly(True)
        # set the layout
        vbox = QtWidgets.QVBoxLayout()
        vboxgr = QtWidgets.QVBoxLayout()
        vboxgr.addWidget(self.canvas)
        vboxgr.addWidget(self.mpl_toolbar)
        vbox.addLayout(vboxgr, 65)
        vbox.addWidget(self.datatext, 20)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.scriptwin, 55)
        hbox.addWidget(self.info, 45)
        vbox.addLayout(hbox,15)
        self.setLayout(vbox)
        self.setTextFont(self.parent.txteditfont)
        self.setWindowTitle(QFileInfo(self.filename).fileName())

        # The FigureCanvas method mpl_connect() returns a connection id
        # which is simply an integer.
        self.canvas.mpl_connect('button_press_event', self.onClick)
        self.canvas.mpl_connect('key_press_event', self.on_key_press)


    def setTextFont(self, font):
        """ Set the font for the all the QTextEdit widgets

        :param font: Font
        :return: nothing
        """
        self.datatext.setFont(font)
        self.info.setFont(font)
        self.scriptwin.setFont(font)


    def on_key_press(self, event):
        # implement the default mpl key press events described at
        # http://matplotlib.org/users/navigation_toolbar.html#navigation-keyboard-shortcuts
        key_press_handler(event, self.canvas, self.mpl_toolbar)


    def onClick(self, event):
        """ Callback function for a user mouse click.

        :param event: mouse event
        :return: nothing
        """
        self.parent.updateUI()
        if event.inaxes:
            if event.button > 1:
                self.parent.raise_()
                self.parent.activateWindow()
                if self.dcursor == None:
                    self.dcursor = dCursor(self)
                self.dcursor.move(event)
                if self.tabledlg is not None:
                    self.tabledlg.table.setCurrentPos(self.dcursor.ic)
                    self.tabledlg.raise_()
                self.parent.updateUI()
                self.setFocus()


    def xToIdx(self, x, blkno=0, xpos=0):
        """ Return the index giving the value closest to 'x'

        :param x: the position
        :param blkno: the data block number
        :param xpos: the position of X data in the data block.
        :return: the closest index.
        """
        if self.xascending:
            tpidx = np.where(self.blklst[blkno][xpos] >= x)
        else:
            tpidx = np.where(self.blklst[blkno][xpos] <= x)
        if tpidx[0].size == 0:
            return None
        return tpidx[0][0]


    def clearMarks(self):
        """ Remove the cursor and all the markers, if any.

        :return: nothing
        """
        if self.dcursor != None:
            self.dcursor = None
        # remove the data markers if any
        del self.markList[:]
        del self.lineList[:]
        # redraw
        self.parent.statusbar.showMessage("")
        self.plotCurves()
        self.parent.updateUI()



    def closeEvent(self, event):
        if (self.dirty and
            QtWidgets.QMessageBox.question(self.parent,
                   "pyDataVis - Unsaved Changes",
                   "Save unsaved changes in {0}?".format(str(self.filename)),
                   QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No) ==
                QtWidgets.QMessageBox.Yes):
            try:
                self.save(self.filename)
            except (IOError, OSError) as err:
                QtWidgets.QMessageBox.warning(self.parent,
                        "pyDataVis -- Save Error",
                        "Failed to save {0}: {1}".format(str(self.filename), err),
                        QtWidgets.QMessageBox.Cancel |
                        QtWidgets.QMessageBox.NoButton |
                        QtWidgets.QMessageBox.NoButton)
        self.parent.numpltw -= 1
        self.parent.updateUI()


    def findNumData(self, txtlines):
        """  Look for the beginning of the data block (skip non numeric data).

             Read the beginning of the file until finding two successive lines
             which contain only numbers. Store the lines before the data
             block in self.header.

        :param txtlines: list of strings containing data.
        :return: The index of the first line of the data block or -1.
        """
        self.vectnames = []
        header = []
        numflg = 0
        for l, line in enumerate(txtlines):
            line = line.strip(' \r\n')
            if line:
                if isNumData(line):
                    numflg += 1
                else:
                    if numflg == 1:
                        # The previous line was numeric but not this one,
                        # therefore reset numflg.
                        numflg = 0
            if numflg < 2:
                header.append(line)
            else:
                break
        if numflg == 2:
            # The last header line contains the first line of the
            # data block, remove it.
            del header[-1]
            l -= 1
            self.headers.append(header)
        else:
            l = -1
        return l


    def setVectorNames(self, sep):
        """ Give a name to the vectors

        :param sep: a character, the column separator
        :return: Nothing
        """
        if self.headers:
            if self.headers[0]:
                items = self.headers[0][-1].split(sep)
                if sep == ' ':
                    # Remove empty elements (case of multiple space separators)
                    items = [x for x in items if x]
                nnam = len(items)
                if nnam == self.nvect and not isNumeric(items):
                    if items[0].startswith('#'):
                        items[0] = items[0][1:]
                    # remove leading and trailing spaces
                    items = [item.strip() for item in items]
                    self.vectnames = items
                    return
        # if the vector names are not provided, name them as Vn
        for i in range(self.nvect):
            self.vectnames.append("V{0}".format(i + 1))



    def fileToString(self, filename):
        """ Convert the text in 'filename' in a string

        :param filename: name of the text file
        :return: A tuple with an error message and a string.
        if no error the error message = "".
        """
        errmsg = ""
        try:
            textfile = open(filename, 'r')
            ftext = textfile.read()
            textfile.close()
        except (IOError, OSError) as err:
            errmsg = err
        except (UnicodeDecodeError) as err:
            try:
                textfile = open(filename, 'r', encoding = 'utf-16')
                ftext = textfile.read()
                textfile.close()
            except (UnicodeDecodeError) as err:
                errmsg = err
        if not errmsg:
            l = len(ftext)
            if l < 1:
                errmsg = "Empty file"
        if errmsg:
           ftext = None
        return (errmsg, ftext)



    def load(self, filename):
        """  Read the data from the file 'filename'.

        :param filename: name of the data file to read.
        :return: if no error, returns an empty string; otherwise an errmsg.
        """

        # Load the file content in self.datatext
        errmsg, txt = self.fileToString(filename)
        if errmsg:
            return errmsg
        self.datatext.setPlainText(txt)
        self.filename = filename
        blocks = None
        self.headers = []
        txtlines = txt.splitlines()
        if len(txtlines) < 2:
            errmsg = "Not enough lines to proceed"
        else:
            # Try with JcampDX format
            errmsg, block, header = JcampDX(txtlines)
            if errmsg == "" and block is not None:
                if len(block):
                    blocks = [block]
                    self.headers.append(header)
                    headers = []
            else:
                startidx = self.findNumData(txtlines)
                if startidx != -1:
                    # Try to guess the column separator
                    if isNumber(txtlines[startidx]):
                        # No separator, 1D data
                        sep = None
                    else:
                        dialect = csv.Sniffer().sniff(txtlines[startidx])
                        sep = dialect.delimiter
                    errmsg = ""
                else:
                    errmsg = "Cannot decode the text data"

        if not errmsg and blocks is None:
            errmsg, blocks, headers = textToData(txtlines[startidx:], sep)
            if blocks is None or len(blocks) == 0 or len(blocks[0][0]) == 0:
                errmsg = 'Unable to decode numeric data'
            else:
                try:
                    for blk in blocks:
                        (self.nvect, self.nelem) = np.shape(np.array(blk))
                except ValueError:
                     errmsg = "Cannot decode the text data"

        if not errmsg:
            self.blklst = []
            for i in range(len(blocks)):
                # convert the list of list in blocks into a list of numpy array
                self.blklst.append(np.array(blocks[i]))
            if len(headers) > 1:
                for header in headers[1:]:
                    self.headers.append(header)
            errmsg = self.initializeCurves()

        if errmsg:
            if self.datatext.toPlainText():
                errmsg += '\nOnly loading text'
            self.info.setText(errmsg)
            errmsg = ""
        else:
            self.updatePlot()
            info = 'Data from {0} loaded'.format(os.path.basename(filename))
            # Display the message in the status bar
            self.parent.statusbar.showMessage(info, 10000)
            self.dirty = False
        return errmsg


    def initializeCurves(self):
        """ Initialize vectors and curves

        :return: an error message (="") if no error
        """

        # Initialize self.vectInfolst from data blocks
        self.initVectInfoList()
        self.curvelist = []
        datatyp = 'unknown'
        errmsg = ""

        # Look for plots commands in the header
        if self.headers:
            cmdlist = []
            for header in self.headers[0]:
                if header.startswith('#plot ') or header.startswith('# plot '):
                    cmdlist.append(header)
                elif header.startswith('#lab') or header.startswith('# lab'):
                    cmdlist.append(header)
                elif header.startswith('#symbol ') or header.startswith('# symbol '):
                    cmdlist.append(header)
                elif header.startswith('#text ') or header.startswith('# text '):
                    cmdlist.append(header)
                elif header.startswith('#arrow ') or header.startswith('# arrow '):
                    cmdlist.append(header)
                elif header.startswith("##DATA TYPE=MASS SPECTRUM"):
                    datatyp = 'MS'
                    self.labx = self.vectInfolst[0][0].name = "Mass"
                    self.laby1 = self.vectInfolst[0][1].name = "Intensity"
                elif header.startswith("##DATA TYPE=INFRARED SPECTRUM"):
                    datatyp = 'line'
                    self.labx = self.vectInfolst[0][0].name = "Wavenumber (/cm)"
                elif header.startswith("##YUNITS=TRANSMITTANCE"):
                    self.laby1 = self.vectInfolst[0][1].name = "Transmittance"
                elif header.startswith("##YUNITS=ABSORBANCE"):
                    self.laby1 = self.vectInfolst[0][1].name = "Absorbance"
                elif header.startswith("##RRUFFID=R"):
                    datatyp = 'line'
                    self.vectInfolst[0][0].name = "Raman_Shift"
                    self.labx = "Raman Shift (/cm)"
                    self.laby1 = self.vectInfolst[0][1].name = "Intensity"
            if cmdlist:
                for cmd in cmdlist:
                    self.plotCmdToCurve(cmd)

        if self.curvelist:
            # check that vector names match curve names
            for curve in self.curvelist:
                curve.yvinfo.name = curve.name

        if self.curvelist == []:
            for blk in range(len(self.blklst)):
                (nvec, npt) = np.shape(self.blklst[blk])
                if nvec > npt and npt < 4:
                    # Most probably data need to be transposed
                    # do not plot anything
                    pass
                else:
                    for i in range(nvec - 1):
                        curvinfo = curveInfo(self.vectInfolst[blk][i+1].name,
                                             self.vectInfolst[blk][0],
                                             self.vectInfolst[blk][i+1])
                        if npt < 15:
                            curvinfo.symbol = True
                        self.curvelist.append(curvinfo)

            if self.curvelist == [] and self.vectInfolst == []:
                errmsg = "Cannot decode the text data"
            else:
                if datatyp == 'MS':
                    self.curvelist[0].plottyp = 'bar'
        return errmsg



    def importSheets(self, filename):
        """  Import spreadsheet data from the file 'filename'.

        :param filename: name of the data file to read.
        :return: if no error, returns an empty string; otherwise an errmsg.
        """

        basenam, ext = os.path.splitext(filename)
        ext = ext.upper()[1:]
        if ext == 'ODS':
            engine = 'odf'
        elif ext.startswith("XL"):
            engine = 'xlrd'
        else:
            return "Unrecognized file extension"

        try:
            sheets = pd.read_excel(filename, sheet_name=None, engine=engine)
        except (IOError, OSError, ImportError) as err:
            return err

        self.blklst = []
        self.headers = []
        for s, sheet in enumerate(sheets):
            # Delete rows where all cells are empty
            df = sheets[sheet]
            df = df.dropna(0, how='all')
            # Delete columns where all cells are empty
            df = df.dropna(1, how='all')
            if df.empty:
                return "No usable numeric data in {0}".format(df[s].key)
            self.blklst.append(df.values)
            # the non numeric first row is supposed to contain vector names
            vnamlst = list(df.values[0])
            if isNumeric(vnamlst):
                vnamlst = list(df.columns.values)
                if isNumeric(vnamlst) or vnamlst[0].startswith("Unnamed"):
                    for i, vnam in enumerate(vnamlst):
                        vnamlst[i] = "V{0}".format(i+1)
            else:
                # remove the non numeric first row
                self.blklst[0] = self.blklst[s][1:]
            self.blklst[s] = self.blklst[s].transpose()
            self.headers.append(['\t'.join(vnamlst)])

        errmsg = self.initializeCurves()
        if not errmsg:
            # Build the text for filling the Text editor window
            text = ""
            n = len(self.blklst)
            for b, blk in enumerate(self.blklst):
                vnames = ""
                for vect in self.vectInfolst[b]:
                    vnames += "{0}\t".format(vect.name)
                text += arrayToString(blk, vnames)
                if b < n-1:
                    text += "\n\n"
            self.datatext.setPlainText(text)

            self.updatePlot()
            info = 'Data from {0} imported'.format(os.path.basename(filename))
            # Display the message in the status bar
            self.parent.statusbar.showMessage(info, 10000)
            self.dirty = False
        return errmsg



    def save(self, filename):
        """ Save the current data in file 'filename'

        :param filename: the name of the file to save.
        :return: False if an error occurred otherwise return True.
        """
        if filename:
            if self.blklst is None:
                # save only the text in datatext
                file = open(filename, 'w')
                file.write(self.datatext.toPlainText())
            else:
                # build the header list
                headers = []
                header = ''
                if self.headers is not None:
                    for line in self.headers[0]:
                        # Do not add plot commands
                        if line.startswith("#plot") or line.startswith("#lab"):
                            break
                        else:
                            header += line + '\n'

                # insert the plot command
                cmdlst = self.curveToPlotCmd(self.curvelist)
                if cmdlst is not None:
                    cmd = "\n#".join(cmdlst)
                    header += '#'+ cmd + '\n'
                # insert the plot commands
                if self.labx is not None:
                    header += '#labX'+ self.labx + '\n'
                if self.laby1 is not None:
                    header += '#labY1'+ self.laby1 + '\n'
                if self.laby2 is not None:
                    header += '#labY2'+ self.laby2 + '\n'
                if self.logX or self.logY:
                    header += '#logaxis {0},{1}\n'.format(int(self.logX), int(self.logY))
                if self.arrows:
                    for arrowprm in self.arrows:
                        header += '#arrow'+ arrowprm + '\n'
                if self.plottext:
                    for txtprm in self.plottext:
                        header += '#text'+ txtprm + '\n'
                if cmdlst is not None:
                    header += '#\n'

                # Insert the line containing vector names
                header += '#'
                for i, nparray in enumerate(self.blklst):
                    for j in range(len(self.vectInfolst[i])):
                        if j > 0:
                            header += '\t'
                        header += self.vectInfolst[i][j].name
                    header += '\n'
                    headers.append(header)
                    header = '#'

                errno, errmsg = dataToFile(filename, self.blklst, headers)
                if errno:
                    QtWidgets.QMessageBox.warning(self.parent, "Save", errmsg,
                                              QtWidgets.QMessageBox.Cancel |
                                              QtWidgets.QMessageBox.NoButton |
                                              QtWidgets.QMessageBox.NoButton)
                else:
                    info = 'Data saved'.format(os.path.basename(filename))
                    self.dirty = False
                    # Display the message in the status bar
                    self.parent.statusbar.showMessage(info, 10000)
            self.dirty = False
            return True
        return False


    def exportToCSV(self, blkno, filename):
        """ Save the data block 'blkno' in file 'filename' with CSV format.

        :param blkno: the number of the data block to save (=0 for the 1st blk).
        :param filename: the name of the file to save.
        :return: False if an error occurred otherwise return True.
        """
        if blkno < 0 or blkno > len(self.blklst):
            return False

        if filename:
            # Build the header containing the vector names
            header = []
            for j in range(len(self.vectInfolst[blkno])):
                header.append(self.vectInfolst[blkno][j].name)
            err = 0
            df = pd.DataFrame(self.blklst[blkno].transpose())
            try:
                df.to_csv(filename, header=header, index=False)
            except (IOError, OSError) as err:
                QtWidgets.QMessageBox.warning(self.parent, "Save", err,
                                                QtWidgets.QMessageBox.Cancel |
                                                QtWidgets.QMessageBox.NoButton |
                                                QtWidgets.QMessageBox.NoButton)
            if not err:
                info = 'Data exported as CSV in {0}'.format(os.path.basename(filename))
                # Display the message in the status bar
                self.parent.statusbar.showMessage(info, 10000)
                return True
            return False



    def getvectInfo(self, noblk, nvect, header):
        """ Try to extract the vector names in the data header
            and initialize a vectInfo list

            The vector names are supposed to be just before the numerical data
            and thus to be in the last line of the header.
            This line should contains as much items as vectors in the block.

        :param noblk: is the index of the data block in the list.
        :param nvect: is the number of vectors in the data block.
        :param header: a list of string
        :return: a list of vectInfo
        """
        lh = len(header)
        vinfolist = []
        if lh > 0:
            # the last line is supposed to contains the vector names
            vnam = header[lh-1].strip()
            if vnam.startswith('#'):
                # remove the # at the beginning
                vnam = vnam[1:]
            vlst = list(vnam.split())
            if vlst:
                if len(vlst) == nvect:
                    # Correct the names containing unauthorized characters
                    charlst = list(' (),;:=-+*/')
                    for i, vnam in enumerate(vlst):
                        for c in charlst:
                            if c in vnam:
                                items = vnam.split(c, 1)
                                vnam = items[0]
                                break
                        vinfo = vectInfo(noblk, i, vnam)
                        vinfolist.append(vinfo)
        return vinfolist


    def autovectInfo(self, noblk, nvect):
        """ Create automatically a vectInfo list associated to a data block.

            The generic name is 'VjBi' where j and i are respectively the
            indexes of the vector and the index of the block whose vector belongs.

        :param noblk: is the index of the data block in the list
        :param nvect: is the number of vectors in the data block
        :return: a list of vectInfo
        """
        vinfolist = []
        for j in range(nvect):
            name = 'V{}B{}'.format(j+1, noblk+1)
            vinfo = vectInfo(noblk, j, name)
            vinfolist.append(vinfo)
        return vinfolist


    def initVectInfoList(self):
        """ Initialize self.vectInfolst from data blocks

        :return: nothing
        """
        vectInfolst = []
        for i, nparray in enumerate(self.blklst):
            nvec, npt = np.shape(nparray)
            vinfolst = self.getvectInfo(i, nvec, self.headers[i])
            if len(vinfolst) != nvec:
                vinfolst = self.autovectInfo(i, nvec)
            else:
                # remove the line with vector names from header
                lh = len(self.headers[i])
                self.headers[i].pop(lh-1)
            vectInfolst.append(vinfolst)
        self.vectInfolst = vectInfolst



    def setDataInfo(self, blklst, vectInfolst):
        """ Create a multiline string containing basic information about the data.

        :param blklst: list of numpy array containing the data
        :param vectInfolst: list of list of vectInfo object
        :return: the 'info' string.
        """
        info = 'Number of data block = {0}\n'.format(len(blklst))
        for i, nparray in enumerate(blklst):
            nvect, nrow = np.shape(nparray)
            info += 'Block {0} : {1} vector(s) of size {2}\n'.format(i+1, nvect, nrow)
            for j, vinfo in enumerate (vectInfolst[i]):
                if j == 0:
                    info += 'Vector names = ' + vectInfolst[i][0].name
                else:
                    info += ', ' + vectInfolst[i][j].name
            info += '\n'
        return info



    def getVinfo(self, vnam, vectInfolst=None):
        """ Find the first vectInfo object in 'vectInfolst' whose name is 'vname'

            If 'vectInfolst' is None use 'self.vectInfolst'.

        :param vnam: name of the searched vector
        :param vectInfolst: list of list of vectInfo objets.
        :return: the vectInfo object or None if not found.
        """
        if not vnam:
            return None
        if vectInfolst is None:
            vectInfolst = self.vectInfolst
        for vinfolst in vectInfolst:
            for vinfo in vinfolst:
                if vinfo.name == vnam:
                    return vinfo
        return None


    def getVnam(self, blkno, vidx, vectInfolst=None):
        """ Find the name of the vector from its block number and position.

            If 'vectInfolst' is None use 'self.vectInfolst'.

        :param blkno: number of the block whose vector belongs
        :param vidx: index of the vector in this block
        :param vectInfolst: list of list of vectInfo objets.
        :return: name of the searched vector
        """

        if vectInfolst is None:
            vectInfolst = self.vectInfolst
        for vinfolst in vectInfolst:
            for vinfo in vinfolst:
                if vinfo.blkpos == blkno:
                    if vinfo.vidx == vidx:
                        return vinfo.name
        return None


    def getCurvinfo(self, cname, curvinfolst=None):
        """ Find the first curveInfo object in 'curvinfolst' whose name is 'cname'

            If 'curvinfolst' is None use 'self.curvelist'.

        :param cname: Name of the searched curveInfo object.
        :param curvinfolst: List of cureInfo objets.
        :return: the curveinfo object or None if not found.
        """
        if curvinfolst is None:
            curvinfolst = self.curvelist
        for curvinfo in curvinfolst:
            if curvinfo.name == cname:
                return curvinfo
        return None



    def plotCurves(self, curvelist=None):
        """ Plot the curves in curvelist

            If 'curvelist' is None use self.curvelist

        :param curvelist: List of the curveInfo objets
        :return: nothing
        """
        if curvelist is None:
            curvelist = self.curvelist
        nc = len(curvelist)
        self.canvas.setFocus()
        self.fig.clf()
        if nc > 0:
            self.axes = self.fig.add_subplot(111)
        else:
            # nothing to plot
            self.canvas.draw()
            return

        if self.invertX:
            self.axes.invert_xaxis()
        if self.invertY:
            self.axes.invert_yaxis()
        self.dplot = []

        # draw the cursor
        if self.dcursor:
            self.dcursor.vl = self.axes.axvline(self.dcursor.xc, color='chocolate')
            if self.curvelist[self.activcurv].axis == 1:
                self.dcursor.hl = self.axes.axhline(self.dcursor.yc, color='chocolate')
            else:
                self.dcursor.hl2 = self.y2axis.axhline(self.dcursor.yc, color='chocolate')
        # draw the data markers
        if len(self.markList):
            for i in range (len(self.markList)):
                self.markList[i].vl = self.axes.axvline(self.markList[i].xc, color='gray')

        # draw the line markers
        if len(self.lineList):
            for i in range (len(self.lineList)):
                self.axes.plot([self.lineList[i].x1,
                                self.lineList[i].x2],
                               [self.lineList[i].y1,
                                self.lineList[i].y2],
                                linewidth=3,
                                color=self.lineList[i].color,
                                linestyle='--')

        # draw the data curves
        for i in range(nc):
            vx = self.blklst[curvelist[i].xvinfo.blkpos][curvelist[i].xvinfo.vidx]
            vy = self.blklst[curvelist[i].yvinfo.blkpos][curvelist[i].yvinfo.vidx]
            if i < len(self.colors):
                color = self.colors[i]
            else:
                color = 'black'
            if curvelist[i].plottyp == 'scat':
                marker = 'o'
            else:
                marker = None
            if curvelist[i].axis == 1:
                if curvelist[i].plottyp == 'bar':
                    self.axes.bar(vx, vy)
                elif curvelist[i].plottyp == 'scat':
                    self.dplot.append(self.axes.scatter(vx, vy,
                                                 color=color,
                                                 marker=marker,
                                                 label=curvelist[i].name))
                else:
                    # plotting against Y1 axis
                    self.dplot.append(self.axes.plot(vx, vy,
                                                 color=color,
                                                 marker=marker,
                                                 label=curvelist[i].name))
            elif curvelist[i].axis == 2:
                # add y2axis
                self.y2axis = self.axes.twinx()
                self.dplot.append(self.y2axis.plot(vx, vy,
                                                   color=color,
                                                   label=curvelist[i].name))

        # Set axis labels
        self.axes.tick_params(axis='x', labelsize='large')
        self.axes.tick_params(axis='y', labelsize='large')
        # put axis legend
        if self.labx is not None:
            self.axes.set_xlabel(self.labx,fontweight='bold', fontsize='large')
        if self.laby1 is not None:
            self.axes.set_ylabel(self.laby1,fontweight='bold', fontsize='large')
        if self.laby2 is not None:
            self.y2axis.set_ylabel(self.laby2, fontweight='bold', fontsize='large')
        # Log scale is set with MatPlotLib toolbar
        #if self.logX:
        #    self.axes.set_xscale('log')
        #if self.logY:
        #    self.axes.set_yscale("log")

        # Set legends
        if nc > 1:
            c = []
            legendlist = []
            for i in range(nc):
                if curvelist[i].plottyp == 'scat':
                    c.append(self.dplot[i])
                else:
                    c.append(self.dplot[i][0])
                legendlist.append(curvelist[i].name)
            self.axes.legend(tuple(c), tuple(legendlist),
                             loc='best', fontsize='large', numpoints=1, shadow=True)
        # draw arrow
        if len(self.arrows):
            for arrw in self.arrows:
                # Arrow function draws arrow from (x, y) to (x + dx, y + dy)
                # x, y, dx, dy, head_width, head_length, color
                prmlst = arrw.split(',')
                if len(prmlst) == 5:
                    xmin, xmax, ymin, ymax = self.axes.axis()
                    if xmin < 0 and xmax > 0:
                        xspan = xmax - xmin
                    else:
                        xspan = xmax - xmin
                    if ymin < 0 and ymax > 0:
                        yspan = ymax - ymin
                    else:
                        yspan = ymax - ymin
                    xpos = float(prmlst[0])
                    ypos = float(prmlst[1])
                    dx = float(prmlst[2])
                    dy = float(prmlst[3])
                    if dx == 0.0:
                        # vertical arrow
                        w = xspan/50.0
                    elif dy == 0.0:
                        # horizontal arrow
                        w = yspan/50.0
                    else:
                        w = xspan/50.0
                    arrw = Arrow(xpos, ypos, dx, dy, width=w, color=prmlst[4], gid='exo')
                    self.axes.add_patch(arrw)

        # print text labels
        if len(self.plottext):
            for txtprm in self.plottext:
                prmlst = txtprm.split(',')
                if len(prmlst) == 5:
                    # xpos, ypos, text, color, fontsize
                    xpos = float(prmlst[0])
                    ypos = float(prmlst[1])
                    fntsiz = int(prmlst[4])
                    self.axes.text(xpos, ypos, prmlst[2], color=prmlst[3], fontsize=fntsiz)

        self.canvas.draw()


    def checkPlotCmd(self, line, curvelist=None):
        """ Check the plot command in 'line'

        :return: an error message (= "" if no error).
        """
        if curvelist is None:
            curvelist = self.curvelist
        if line.startswith('plot'):
            items = line[5:].split(',')
            l = len(items)
            if l < 2 or l > 3 or (l == 3 and items[2] != '2'):
                return "Accept only two vectors"
            else:
                v1nam = items[0]
                v1info = self.getVinfo(v1nam.strip())
                v2nam = items[1]
                v2info = self.getVinfo(v2nam.strip())
                if v1info is None or v2info is None:
                    return "Unknown vector name"
                if v1info.blkpos != v2info.blkpos:
                    return "{0} and {1} must belong to the same data block".format(v1nam, v2nam)
                return ""

        elif line.startswith('lab'):
            items = line[3:].split(' ')
            if len(items) < 2:
                return "Missing axis label"
            else:
                if not items[0] in ['X', 'Y1', 'Y2']:
                    return "Accept only either labX, labY1 or labY2"
                if items[0] == 'Y2' and self.y2axis is None:
                    return "No secondary Y axis"
                return ""

        elif line.startswith('symbol'):
            items = line.split(' ')
            if len(items) != 2:
                return "One parameter is required"
            curvinfo = self.getCurvinfo(items[1].strip(), curvelist)
            if curvinfo is not None:
                return ""
            else:
                return (1, "Wrong curve name")

        elif line.startswith('nosymbol'):
            items = line.split(' ')
            if len(items) != 2:
                return "Only one parameters is required"
            curvinfo = self.getCurvinfo(items[1].strip(), curvelist)
            if curvinfo is not None:
                return ""
            else:
                return (1, "Wrong curve name")

        elif line.startswith('logaxis'):
            items = line[8:].split(',')
            if len(items) != 2:
                return "Two values are required"
            if isNumber(items[0]) and isNumber(items[1]):
                if int(items[0]) == 0 or int(items[1]) == 0 or \
                        int(items[0]) == 1 or int(items[1]) == 1:
                    return ""
            return "Only 0 or 1 are allowed"

        elif line.startswith('arrow'):
            items = line[6:].split(',')
            if len(items) != 5:
                return "Accept only 5 parameters"
            else:
                # xpos, ypos, dx, dy, color
                if isNumber(items[0]):
                    xpos = float(items[0])
                else:
                    return "X position should be a number"
                if isNumber(items[1]):
                    ypos = float(items[1])
                else:
                    return "Y position should be a number"
                if isNumber(items[2]):
                    dx = float(items[2])
                else:
                    return "dx should be a number"
                if isNumber(items[3]):
                    dy = float(items[3])
                else:
                    return "dy should be a number"
                if not items[4] in self.colors:
                    return "Unknown color"
                else:
                    return ""

        elif line.startswith('text'):
            items = line[5:].split(',')
            if len(items) != 5:
                return "Accept only 5 parameters"
            else:
                # xpos, ypos, text, color, fontsize
                if isNumber(items[0]):
                    xpos = float(items[0])
                else:
                    return "X position should be a number"
                if isNumber(items[1]):
                    ypos = float(items[1])
                else:
                    return "Y position should be a number"
                if self.axes is not None:
                    xmin, xmax, ymin, ymax = self.axes.axis()
                    if xpos < xmin or xpos > xmax:
                         return "X position is incorrect"
                    if ypos < ymin or ypos > ymax:
                         return "Y position is incorrect"
                color = items[3]
                if not color in self.colors:
                    return "Unknown color"
                if not isNumber(items[4]):
                    return "Font size should be a number"
                else:
                    fntsiz = int(items[4])
                    if fntsiz < 2 or fntsiz > 50:
                        return "Font size should be in the range 2-50"
                    else:
                        return ""
        else:
            return "Unknown plot command"




    def plotCmdToCurve(self, cmd):
        """ Create or modify a 'curveinfo' object from the plot command 'cmd'.

            This function is the symmetric of curveToPlotCmd.

        :param cmd: a string containing the plot command.
        :return: the curveinfo object or None in case of error.
        """
        errmsg = ""
        # remove # for plot command coming from file
        if cmd.startswith('#'):
            cmd = cmd[1:]
            cmd = cmd.strip()

        # axes labels
        if cmd.startswith('lab'):
            params = cmd[3:]
            items = params.split(' ')
            if items[0] == 'X':
                self.labx = params[1:]
            elif items[0] == 'Y1':
                self.laby1 = params[2:]
            elif items[0] == 'Y2':
                self.laby2 = params[2:]

        elif cmd.startswith('plot'):
            params = cmd[5:]
            items = params.split(',')
            for i in range(2):
                vnam = items[i]
                vinfo = self.getVinfo(vnam.strip())
                if vinfo is not None:
                    if i == 0:
                        xvinfo = vinfo
                    else:
                        cinfo = curveInfo(vnam, xvinfo, vinfo)
                        cinfo.axis = 1
                        if len(items) > 2:
                            cinfo.axis = int(items[2])
                        if self.blklst[xvinfo.blkpos][xvinfo.vidx].size < 15:
                            cinfo.symbol = True
                        self.curvelist.append(cinfo)
                else:
                    errmsg = "Unknown vector name {0}".format(vnam)
                    break

        elif cmd.startswith('logaxis'):
            params = cmd[8:]
            items = params.split(',')
            self.logX = int(items[0]) != 0
            self.logY = int(items[1]) != 0

        elif cmd.startswith('text'):
            if self.checkPlotCmd(cmd) == "":
                self.plottext.append(cmd[4:])

        elif cmd.startswith('arrow'):
            if self.checkPlotCmd(cmd) == "":
                self.arrows.append(cmd[5:])

        elif cmd.startswith('symbol'):
            if self.checkPlotCmd(cmd) == "":
                items = cmd.split(' ')
                if len(items) == 2:
                    curvinfo = self.getCurvinfo(items[1])
                    if curvinfo is not None:
                        curvinfo.plottyp = 'scat'

        elif cmd.startswith('nosymbol'):
            if self.checkPlotCmd(cmd) == "":
                items = cmd.split(' ')
                if len(items) == 2:
                    curvinfo = self.getCurvinfo(items[1])
                    if curvinfo is not None:
                        curvinfo.plottyp = 'line'

        else:
            errmsg = "Unknown plot command"
        if errmsg:
            QtWidgets.QMessageBox.warning(self.parent, "Plot", errmsg,
                                        QtWidgets.QMessageBox.Cancel |
                                        QtWidgets.QMessageBox.NoButton |
                                        QtWidgets.QMessageBox.NoButton)




    def curveToPlotCmd(self, curvlist=None):
        """ Create a plot command list from the list 'curvlist'.

            This function is the symmetric of plotCmdToCurve.
            If 'curvlist' is None use self.curvelist.

        :param curvlist: a list of curveInfo objets.
        :return: the plot command list or None if there is no curve in list.
        """
        if curvlist is None:
            curvlist = self.curvelist
        if len(curvlist) == 0:
            return None
        cmdlist = []
        for curve in curvlist:
            cmd = 'plot ' + curve.xvinfo.name + ',' + curve.yvinfo.name
            if curve.axis != 1 and len(curvlist) > 1:
                cmd += ',' + str(curve.axis)
            cmdlist.append(cmd)
            if curve.plottyp == 'scat':
                cmd = "symbol {0}".format(curve.name)
                cmdlist.append(cmd)
        return cmdlist



    def checkPlotOrder(self, plotlist):
        """  Test if the first plot command is against Y1

        :param plotlist: a list of plot command
        :return: an error message (= "" if no error)
        """
        Y1flg = False
        for cmd in plotlist:
            if cmd.startswith("plot"):
                params = cmd[5:]
                items = params.split(',')
                l = len(items)
                if l == 2 and not Y1flg:
                    # it is a plot against Y1
                    Y1flg = True
                else:
                    if l == 3 and Y1flg == False:
                        return "Plot first against primary Y-axis"
        return ""



    def scriptPlot(self, cmdlist):
        """ Plot or update the curves from the plot command list 'cmdlist'.

        :param cmdlist: a list of plot command.
        :return: nothing
        """
        if cmdlist:
            if cmdlist[0].startswith("plot"):
                # if it is a plot command, clear previous curves
                self.curvelist = []
            for cmd in cmdlist:
                self.plotCmdToCurve(cmd)
            self.updatePlot()


    def displayInfo(self):
        """ Display info on the current data in the information window.

        :return: nothing
        """
        if self.blklst is None:
            return ""
        else:
            info = self.setDataInfo(self.blklst, self.vectInfolst)
            plotcmdlst = self.curveToPlotCmd()
            if plotcmdlst is not None:
                info += '\n'.join(plotcmdlst)
        self.info.setText(info)


    def updatePlot(self):
        """ Display info on data and plot self.curvelist curves.

        :return: nothing.
        """
        self.displayInfo()
        if self.curvelist:
            if self.dcursor is not None:
                self.dcursor.updateCurve()
            else:
                blkno = self.curvelist[self.activcurv].xvinfo.blkpos
                xpos = self.curvelist[self.activcurv].xvinfo.vidx
                X = self.blklst[blkno][xpos]
                self.xascending = (X[X.size - 1] > X[0])
        self.plotCurves(self.curvelist)


    def delBlock(self, blkno):
        """ Delete the data block having index 'blkno'.

        :param blkno: the data block number
        :return:  True if done, False otherwise.
        """
        # check the parameters
        if blkno < 0 or blkno >= len(self.blklst):
            return False

        vinfolst = self.vectInfolst[blkno]
        # update self.curvelist
        for vinfo in vinfolst:
            for curve in self.curvelist:
                if curve.xvinfo == vinfo:
                    self.curvelist.remove(curve)
                    break
            for curve in self.curvelist:
                if curve.yvinfo == vinfo:
                    self.curvelist.remove(curve)
                    break

        # delete the vectorInfolst in self.vectInfolst
        del self.vectInfolst[blkno]

        # delete the data block
        del self.blklst[blkno]

        self.dirty = True
        self.updatePlot()
        return True


    def delVector(self, blkno, vpos):
        """ Delete the vector having the index 'vpos' in the block 'blkno'

        :param blkno: the data block number containing the vector
        :param vpos: the index of the vector in the data block.
        :return:  True if done, False otherwise.
        """
        # check the parameters
        if blkno < 0 or blkno >= len(self.blklst):
            return False
        nvect, nrow = np.shape(self.blklst[blkno])
        if vpos < 0 or vpos >= nvect:
            return False

        # find the vector in self.vectInfolst[blkno]
        infolst = self.vectInfolst[blkno]
        for vinfo in infolst:
            if vinfo.vidx == vpos and vinfo.blkpos == blkno:
                vectinfo = vinfo

        # delete the vector
        if nvect == 1:
            # It the vector is the only one in the data block
            # delete the data block
            del self.blklst[blkno]
        else:
            newset = np.vstack((self.blklst[blkno][:vpos], self.blklst[blkno][vpos+1:]))
            self.blklst[blkno] = newset

        # update self.vectInfolst
        for vinfo in infolst:
            if vinfo.vidx == vpos:
                infolst.remove(vinfo)
                break
        for vinfo in infolst:
            if vinfo.vidx > vpos:
                vinfo.vidx -= 1
        # update self.curvelist
        for curve in self.curvelist:
            if curve.xvinfo == vectinfo:
                self.curvelist.remove(curve)
                break
        for curve in self.curvelist:
            if curve.yvinfo == vectinfo:
                self.curvelist.remove(curve)
                break
        self.dirty = True
        self.updatePlot()
        return True


    def delCurve(self, cpos):
        """  Delete the curve having the index 'cpos' in self.curvelist

        :param cpos: index of the curve in self.curvelist.
        :return: True if done, False otherwise.
        """
        if len(self.curvelist) == 0:
            return False
        # check the parameters
        if cpos < 0 or cpos >= len(self.curvelist):
            return False
        xvinfo = self.curvelist[cpos].xvinfo
        yvinfo = self.curvelist[cpos].yvinfo
        blkno = yvinfo.blkpos
        nvect, nrow = np.shape(self.blklst[blkno])
        delx = True       # used to check if X will be deleted
        delblk = False
        # If X and Y vectors are the only ones in the block,
        # delete the whole block
        if nvect == 2:
            del self.blklst[blkno]
            delblk = True
        else:
            # Check if the vector X is used by another curve
            for curve in self.curvelist:
                if curve.xvinfo == xvinfo:
                    delx = False
                    break
            # If not find, delete the vector X
            if delx:
                newset = np.vstack((self.blklst[blkno][:xvinfo.vidx],
                                    self.blklst[blkno][xvinfo.vidx + 1:]))
                self.blklst[blkno] = newset
            # delete the vector Y
            newset = np.vstack((self.blklst[blkno][:yvinfo.vidx],
                                self.blklst[blkno][yvinfo.vidx + 1:]))
            self.blklst[blkno] = newset

        # update vector index in self.vectInfolst
        infolst = self.vectInfolst[blkno]
        if delx:
            for vinfo in infolst:
                if vinfo.vidx == xvinfo.vidx:
                    infolst.remove(vinfo)
                    break
            for vinfo in infolst:
                   if vinfo.vidx != yvinfo.vidx and vinfo.vidx > xvinfo.vidx:
                       vinfo.vidx -= 1
        for vinfo in infolst:
            if vinfo.vidx == yvinfo.vidx:
                infolst.remove(vinfo)
                break
        for vinfo in infolst:
            if vinfo.vidx > yvinfo.vidx:
                vinfo.vidx -= 1

        # update blkno position if a whole block was deleted
        if delblk:
            delidx = None
            for i, vinfolist in enumerate(self.vectInfolst):
                if not vinfolist:
                    delidx = i
                else:
                    for vinfo in vinfolist:
                        if vinfo.blkpos > blkno:
                             vinfo.blkpos -= 1
            if delidx is not None:
                del self.vectInfolst[delidx]

        # update self.curvelist
        if delx:
            for curve in self.curvelist:
                if curve.xvinfo == xvinfo:
                    self.curvelist.remove(curve)
                    break
        for curve in self.curvelist:
            if curve.yvinfo == yvinfo:
                self.curvelist.remove(curve)
                break
        self.dirty = True
        self.updatePlot()
        if self.tabledlg is not None:
            self.tabledlg.table.initTable()
        return True


    def pasteVector(self, vect, blkno, vname):
        """ Paste the vector 'vect' at the end of the block 'blkno'

        :param vect: a 1D ndarray containing the vector elements.
        :param blkno: the data block number where the new vector will be added.
        :param vname: the vector name.
        :return: True if done, False otherwise.
        """
        (nvect, npt) = np.shape(self.blklst[blkno])
        if vect.size != npt:
            QtWidgets.QMessageBox.warning(self.parent, "Paste a vector",
                                      "Incompatible size of the vector in memory",
                                      QtWidgets.QMessageBox.Cancel |
                                      QtWidgets.QMessageBox.NoButton |
                                      QtWidgets.QMessageBox.NoButton)
            return False
        newset = np.vstack((self.blklst[blkno], vect))
        self.blklst[blkno] = newset
        vinfo = self.getVinfo(vname)
        if vinfo is not None:
            # If the name already exists, prepends the name with #
            vname += '#'
        # update self.vectInfolst
        infolst = self.vectInfolst[blkno]
        # Create a new vectInfo object and append it to the list.
        vinfo = vectInfo(blkno, nvect, vname)
        infolst.append(vinfo)
        self.dirty = True
        return True


    def duplicateCurve(self, cidx):
        """ Duplicate the curve having the index 'cidx' in self.curvelist

        :param cidx: the index of the curve in self.curvelist.
        :return: True if done, False otherwise.
        """
        cname = self.curvelist[cidx].name + '#'
        xvinfo = self.curvelist[cidx].xvinfo
        yvinfo = self.curvelist[cidx].yvinfo
        blkno = yvinfo.blkpos
        if self.pasteVector(self.blklst[blkno][yvinfo.vidx], blkno, cname):
            yvinfo = self.getVinfo(cname)
            self.curvelist.append(curveInfo(cname, xvinfo, yvinfo))
            self.plotCurves()
            self.displayInfo()
            if self.tabledlg is not None:
                self.tabledlg.table.initTable()
            self.parent.updateUI()


    def pasteCurve(self, vectX, xnam, vectY, ynam):
        """ Add a curve in the current plotWindow

            If vectX already existing in the block add only vectY
            at the end of the block 'blkno' otherwise create a new
            data block.

        :param vectX: a 1D ndarray containing the X vector elements.
        :param xnam: the name of X vector.
        :param vectY: a 1D ndarray containing the Y vector elements.
        :param ynam: the name of the Y vector.
        :return: True if done, False otherwise.
        """
        title = "Paste a curve"
        blkno = None
        xidx = 0
        done = False
        if self.blklst is None:
            self.blklst = []
        else:
            # If the Y vector name is already existing add the suffix '#'
            while True:
                vinfo = self.getVinfo(ynam)
                if vinfo is not None:
                    ynam += '#'
                else:
                    break
            # check if the 'vectX' is already existing in a data block
            for n, nparray in enumerate(self.blklst):
                if blkno is not None:
                    break
                nvect, npt = np.shape(self.blklst[0])
                for i in range(nvect):
                    if np.allclose(vectX, nparray[i]):
                        blkno = n
                        xidx = i
                        break
            if blkno is not None:
                # vectX already existing, ask user to add vectY
                # at the end of self.blklst[blkno]
                msg = "Add this data as a new vector in current data block ?"
                reply = QtWidgets.QMessageBox.question(self, title,
                                      msg, QtWidgets.QMessageBox.Yes |
                                      QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
                if reply == QtWidgets.QMessageBox.Yes:
                    newset = np.vstack((self.blklst[blkno], vectY))
                    self.blklst[blkno] = newset
                    # update self.vectInfolst and self.curvelist
                    xnam = self.getVnam(blkno, xidx)
                    if xnam is not None:
                        vx = vectInfo(blkno, xidx, xnam)
                        vy = vectInfo(blkno, nvect, ynam)
                        self.vectInfolst[blkno].append(vy)
                        self.curvelist.append(curveInfo(ynam, vx, vy))
                        done = True
        if not done:
            # Create a new data block to store vectX and vectY.
            newset = np.vstack((vectX, vectY))
            self.blklst.append(newset)
            blkno = len(self.blklst)-1
            # If the X vector name is already existing add the suffix '#'
            while True:
                vinfo = self.getVinfo(xnam)
                if vinfo is not None:
                    xnam += '#'
                else:
                    break
            # update self.vectInfolst and self.curvelist
            vinfolst = []
            vx = vectInfo(blkno, 0, xnam)
            vy = vectInfo(blkno, 1, ynam)
            vinfolst.append(vx)
            vinfolst.append(vy)
            self.vectInfolst.append(vinfolst)
            self.curvelist.append(curveInfo(ynam, vx, vy))
            done = True
        if done:
            self.dirty = True
            self.plotCurves()
            if self.tabledlg is not None:
                self.tabledlg.table.initTable()
            self.displayInfo()
        return done


    def saveCurveInFile(self, cpos, filename):
        """ Save a curve (X,Y vector pair) in a file

        :param cpos: the index of the curve in self.curvelist
        :param filename: name of the file in which curve data will be saved.
        :return: True if success, False otherwise.
        """
        if filename:
            if self.blklst is not None:
                xvinfo = self.curvelist[cpos].xvinfo
                yvinfo = self.curvelist[cpos].yvinfo
                blkno = yvinfo.blkpos
                # build a new array by stacking X and Y vectors
                newdata = np.vstack((self.blklst[blkno][xvinfo.vidx],
                                     self.blklst[blkno][yvinfo.vidx]))
                # save the data in the file
                vnames = xvinfo.name + '\t' + yvinfo.name
                np.savetxt(filename, np.transpose(newdata), header=vnames)
                return True
        return False
