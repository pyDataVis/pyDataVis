""" This module contains the Dialogs for interactive Tools menu
"""
from PyQt5.QtCore import Qt, QRegExp
from PyQt5 import QtGui, QtWidgets

import datetime
import numpy as np
from operator import itemgetter
from scipy.optimize import leastsq
from scipy import interpolate, signal
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)

from utils import (isNumber, calcArea, round_to_n, getSpan, MovAver)
from plotWindow import vectInfo, curveInfo



# smoothDlg ------------------------------------------------------------

class smoothDlg(QtWidgets.QDialog):
    def __init__(self, parent=None, pltw=None, cpos=None):
        """ Interactive Smoothing Tool dialog.

        :param parent: pyDataVis MainWindow.
        :param cpos: it is the curve position in plotWin.curvelist.
        """
        super (smoothDlg, self).__init__(parent)

        self.parent = parent
        self.pltw = pltw
        self.cpos = cpos
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.canvas.setFocus()
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)

        self.axes = self.fig.add_subplot(111)
        # Type
        typelab = QtWidgets.QLabel("Type")
        self.typeComboBox = QtWidgets.QComboBox(self)
        self.typelist = [ "Moving average", "Savitzky-Golay" ]
        self.typeComboBox.addItems(self.typelist)
        # Filter
        filterlab = QtWidgets.QLabel("Filter size")
        self.filterComboBox = QtWidgets.QComboBox(self)
        oddlst = range(5, 300, 2)  # list of odd integers between 5 and 100
        self.filterlist = [str(i) for i in oddlst]
        self.filterComboBox.addItems(self.filterlist)
        # order
        self.orderlab = QtWidgets.QLabel("Order")
        self.orderSpinBox = QtWidgets.QSpinBox(self)
        self.orderSpinBox.setMinimum(1)
        self.orderSpinBox.setMaximum(12)
        # Number of pass
        self.nbpasslab = QtWidgets.QLabel("Number of pass")
        self.nbpassSpinBox = QtWidgets.QSpinBox(self)
        self.nbpassSpinBox.setMaximum(50)
        # Buttons
        exeBtn = QtWidgets.QPushButton("Compute")
        okBtn = QtWidgets.QPushButton("OK")
        cancelBtn = QtWidgets.QPushButton("Cancel")

        # set the layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        hbox1 = QtWidgets.QHBoxLayout()
        hbox1.addWidget(typelab)
        hbox1.addWidget(self.typeComboBox)
        hbox1.addWidget(filterlab)
        hbox1.addWidget(self.filterComboBox)
        hbox1.addWidget(self.orderlab)
        hbox1.addWidget(self.orderSpinBox)
        hbox1.addWidget(self.nbpasslab)
        hbox1.addWidget(self.nbpassSpinBox)
        hbox2 = QtWidgets.QHBoxLayout()
        hbox2.addWidget(exeBtn)
        hbox2.addWidget(okBtn)
        hbox2.addWidget(cancelBtn)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        self.setLayout(vbox)

        # Connect buttons to callback functions
        self.typeComboBox.currentIndexChanged.connect(self.changeType)
        self.orderSpinBox.valueChanged.connect(self.changeOrder)
        exeBtn.clicked.connect(self.compute)
        okBtn.clicked.connect(self.validate)
        cancelBtn.clicked.connect(self.reject)
        self.setWindowTitle('Smoothing tool')

        self.initDlg(cpos)



    def initDlg(self, cpos):
        """ Initialize the dialog.

        :param cpos: it is the curve position in plotWin.curvelist.
        :return: nothing
        """
        self.blkno = self.pltw.curvelist[cpos].yvinfo.blkpos
        self.xpos = self.pltw.curvelist[cpos].xvinfo.vidx
        self.ypos = self.pltw.curvelist[cpos].yvinfo.vidx
        # Create 3 vectors:
        # y1 = initial data, y2 = smoothed data, y3 = y2 - y1
        self.data = np.vstack( (self.pltw.blklst[self.blkno][self.xpos],
                                self.pltw.blklst[self.blkno][self.ypos],
                                self.pltw.blklst[self.blkno][self.ypos],
                                np.zeros(len(self.pltw.blklst[self.blkno][self.xpos]))) )
        self.type = self.parent.smoothtyp
        self.nfilter = self.parent.smoothFilter
        self.npass = self.parent.smoothpass
        if self.nfilter < 7:
            self.order = self.nfilter - 2
            if self.order < 1:
                self.order = 1
        else:
            self.order = 2
        # Calculate the magnitude of negative shift to apply to the
        # difference between initial and smoothed values.
        self.diffshift = getSpan(self.data[1]) * 0.2
        if self.data[1].min() + self.diffshift < 0.0:
            self.diffshift *= -1.0
        self.first = True

        self.typeComboBox.setCurrentIndex(self.type)
        cbidx = self.filterlist.index(str(self.nfilter))
        self.filterComboBox.setCurrentIndex(cbidx)
        self.orderSpinBox.setValue(self.order)
        self.nbpassSpinBox.setValue(self.npass)
        self.compute()


    def changeOrder(self):
        """ Callback function for self.orderSpinBox

        :return: nothing
        """
        order = self.orderSpinBox.value()
        nfilter = int(str(self.filterComboBox.currentText()))
        if order > nfilter - 2:
            order = nfilter - 2
        if order < 1:
            order = 1
        self.orderSpinBox.setValue(order)
        self.order = order


    def changeType(self):
        """ Callback function for self.typeComboBox

        :return: nothing
        """
        type = self.typeComboBox.currentIndex()
        if type == 0:
            # For Moving Average, disable orderSpinBox and orderlab
            self.orderSpinBox.setEnabled(False)
            self.orderlab.setEnabled(False)
        else:
            self.orderSpinBox.setEnabled(True)
            self.orderlab.setEnabled(True)


    def compute(self):
        """ Apply the smoothing algorithm according to the smoothing type.

        :return: nothing
        """
        # get the values in widgets
        if self.first:
            self.first = False
            type = self.type
            nfilter = self.nfilter
            order = self.order
            npass = self.npass
        else:
            type = self.typeComboBox.currentIndex()
            nfilter = int(str(self.filterComboBox.currentText()))
            order = self.orderSpinBox.value()
            npass = self.nbpassSpinBox.value()
            self.data[2] = self.data[1]        # Restore initial values
        for i in range(npass):
            if type == 0:
                self.data[2] = MovAver(self.data[2], nfilter)
            else:
                self.data[2] = signal.savgol_filter(self.data[2],
                                                    window_length = nfilter,
                                                    polyorder = order)
        self.data[3] = self.data[2] - self.data[1] - self.diffshift
        self.type = type
        self.nfilter = nfilter
        self.npass = npass
        if type == 1:
            self.order = order
        self.updatePlot()


    def updatePlot(self):
        """ Update the plotting area.

            Plot 3 curves: y1 = initial data, y2 = smoothed data, y3 = y2 - y1
        :return: nothing
        """
        self.axes.clear()
        self.axes.plot(self.data[0], self.data[1], linestyle='-', color='gray')
        self.axes.plot(self.data[0], self.data[2], linestyle='-', color='blue')
        self.axes.plot(self.data[0], self.data[3], linestyle='-', color='darkgreen')
        self.canvas.draw()


    def validate(self):
        """ Callback function when user has clicked on OK button.

        :return: nothing
        """
        self.parent.copyCurrentWinState(self.pltw)
        self.pltw.blklst[self.blkno][self.ypos] = self.data[2]
        self.pltw.dirty = True
        self.pltw.activecurv = self.cpos
        self.pltw.updatePlot()
        self.parent.smoothtyp = self.type
        self.parent.smoothFilter = self.nfilter
        self.parent.smoothpass = self.npass
        self.parent.updateUI()
        self.hide()


#  splinSmoothDlg ------------------------------------------------------------

class splinSmoothDlg(QtWidgets.QDialog):
    def __init__(self, parent=None, pltw=None, cpos=None):
        """ Interactive Spline Smoothing Tool dialog.

        :param parent: pyDataVis MainWindow.
        :param cpos: it is the curve position in plotWin.curvelist.
        """
        super (splinSmoothDlg, self).__init__(parent)

        self.parent = parent
        self.pltw = pltw
        self.cpos = cpos
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.canvas.setFocus()
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)

        self.axes = self.fig.add_subplot(111)
        # k is the degree of the smoothing spline. Must be <= 5.
        klab = QtWidgets.QLabel("Degree of spine")
        self.kComboBox = QtWidgets.QComboBox(self)
        klst = [2, 3, 4, 5]
        self.klist = [str(i) for i in klst]
        self.kComboBox.addItems(self.klist)
        # s is the smoothing factor, must be positive
        slab = QtWidgets.QLabel("Smoothing factor")
        self.stext = QtWidgets.QLineEdit(self)
        regex = QRegExp("[0-9][.0-9][0-9][0-9]")
        validator = QtGui.QRegExpValidator(regex)
        self.stext.setValidator(validator)

        # Buttons
        exeBtn = QtWidgets.QPushButton("Compute")
        okBtn = QtWidgets.QPushButton("OK")
        cancelBtn = QtWidgets.QPushButton("Cancel")

        # set the layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        hbox1 = QtWidgets.QHBoxLayout()
        hbox1.addWidget(klab)
        hbox1.addWidget(self.kComboBox)
        hbox1.addWidget(slab)
        hbox1.addWidget(self.stext)
        hbox2 = QtWidgets.QHBoxLayout()
        hbox2.addWidget(exeBtn)
        hbox2.addWidget(okBtn)
        hbox2.addWidget(cancelBtn)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        self.setLayout(vbox)

        # Connect buttons to callback functions
        exeBtn.clicked.connect(self.compute)
        okBtn.clicked.connect(self.validate)
        cancelBtn.clicked.connect(self.reject)
        self.setWindowTitle('Spline Smoothing tool')
        self.initDlg(cpos)


    def initDlg(self, cpos):
        """ Initialize the dialog.

        :param cpos: it is the curve position in plotWin.curvelist.
        :return: nothing
        """
        self.blkno = self.pltw.curvelist[cpos].yvinfo.blkpos
        self.xpos = self.pltw.curvelist[cpos].xvinfo.vidx
        self.ypos = self.pltw.curvelist[cpos].yvinfo.vidx
        # Create 3 vectors:
        # y1 = initial data, y2 = smoothed data, y3 = y2 - y1
        self.data = np.vstack( (self.pltw.blklst[self.blkno][self.xpos],
                                self.pltw.blklst[self.blkno][self.ypos],
                                self.pltw.blklst[self.blkno][self.ypos],
                                np.zeros(len(self.pltw.blklst[self.blkno][self.xpos]))) )
        self.npt = self.data[0].size
        self.yspan = self.data[1].max() - self.data[1].min()
        self.incr = True
        # Sort data in ascending order because  interpolate.UnivariateSpline
        # function does not work in descending order.
        if self.data[0][0] > self.data[0][self.npt-1]:
            self.incr = False
            self.data[0] = self.data[0][::-1]
            self.data[1] = self.data[1][::-1]

        self.k = 3
        self.s = 1.0
        self.diffshift = getSpan(self.data[1]) * 0.2
        if self.data[1].min() + self.diffshift < 0.0:
            self.diffshift *= -1.0
        self.first = True

        kidx = self.klist.index("3")
        self.kComboBox.setCurrentIndex(kidx)
        self.stext.setText(str(self.s))
        self.compute()


    def get_k(self):
        """ Give to self.k the value of k from self.kComboBox.

        :return: nothing
        """
        kidx = self.kComboBox.currentIndex()
        self.k = int(self.klist[kidx])

    def get_s(self):
        """ Give to self.s the value of s from self.stext.

        :return: noting
        """
        st = self.stext.text()
        self.s = float(st)


    def compute(self):
        """ Apply the spline smoothing algorithm.

        :return: nothing
        """
        # get the values in widgets
        if self.first:
            self.first = False
        else:
            self.get_k()
            self.get_s()
            self.data[2] = self.data[1]        # Restore initial values

        spl = interpolate.UnivariateSpline(self.data[0], self.data[1], k=self.k)
        s = self.s * self.yspan
        spl.set_smoothing_factor(s)
        self.data[2] = spl(self.data[0])

        # Compute the RMSE
        RMSE = np.sqrt(np.square(self.data[1] - self.data[2]).sum() / self.npt)
        self.data[3] = self.data[2] - self.data[1] - self.diffshift
        self.updatePlot()


    def updatePlot(self):
        """ Update the plotting area.

            Plot 3 curves: y1 = initial data, y2 = smoothed data, y3 = y2 - y1
        :return: nothing
        """
        self.axes.clear()
        self.axes.plot(self.data[0], self.data[1], linestyle='-', color='gray')
        self.axes.plot(self.data[0], self.data[2], linestyle='-', color='blue')
        self.axes.plot(self.data[0], self.data[3], linestyle='-', color='darkgreen')
        self.canvas.draw()


    def validate(self):
        """ Callback function when user has clicked on OK button.

        :return: nothing
        """
        self.parent.copyCurrentWinState(self.pltw)
        if self.incr:
            self.pltw.blklst[self.blkno][self.ypos] = self.data[2]
        else:
            self.pltw.blklst[self.blkno][self.ypos] = self.data[2][::-1]
        self.pltw.dirty = True
        self.pltw.activecurv = self.cpos
        self.pltw.updatePlot()
        self.parent.updateUI()
        self.hide()


# ALS_SmoothDlg --------------------------------------------------------------

# Baseline Correction with Asymmetric Least Squares Smoothing
# Method of Paul Eilers and Hans Boelens (2005)
# Creates (and overwrites) w_base, a baseline estimate for w_data. The
# asymmetry parameter (Eilers and Boelens' p) generally takes values
# between 0.001 and 0.1. Try varying lambda in orders of magnitude
# between 10^2 and 10^9. Not efficient for large N, try it for w_data
# with fewer than 1000 points.

from scipy import sparse
from scipy.sparse.linalg import spsolve

class ALS_SmoothDlg(QtWidgets.QDialog):
    """ Interactive ALS Smoothing Tool dialog.

    :param parent: pyDataVis MainWindow.
    :param cpos: it is the curve position in plotWin.curvelist.
    """
    def __init__(self, parent=None, pltw=None, cpos=None):
        super (ALS_SmoothDlg, self).__init__(parent)

        self.parent = parent
        self.pltw = pltw
        self.cpos = cpos
        self.blkno = self.pltw.curvelist[cpos].yvinfo.blkpos
        self.xpos = self.pltw.curvelist[cpos].xvinfo.vidx
        self.ypos = self.pltw.curvelist[cpos].yvinfo.vidx
        self.npt = self.pltw.blklst[self.blkno][self.xpos].size
        self.data = np.vstack( (self.pltw.blklst[self.blkno][self.xpos],
                                self.pltw.blklst[self.blkno][self.ypos],
                                np.zeros(len(self.pltw.blklst[self.blkno][self.xpos]))) )
        self.lambd = 1e5
        self.p = 0.01

        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.canvas.setFocus()
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)

        self.axes = self.fig.add_subplot(111)
        # Lambda
        lambdlab = QtWidgets.QLabel("Lambda")
        self.lambdtext = QtWidgets.QLineEdit(self)
        regex = QRegExp("[0-9]+.?[0-9]{,0}")
        validator = QtGui.QRegExpValidator(regex, self.lambdtext)
        self.lambdtext.setValidator(validator)
        # p
        plab = QtWidgets.QLabel("p")
        self.ptext = QtWidgets.QLineEdit(self)
        regex = QRegExp("[0-9]+.?[0-9]{,6}")
        validator = QtGui.QRegExpValidator(regex, self.ptext)
        self.ptext.setValidator(validator)
        # Buttons
        exeBtn = QtWidgets.QPushButton("Compute")
        subBtn = QtWidgets.QPushButton("Subtract")
        addBtn = QtWidgets.QPushButton("Add")
        cancelBtn = QtWidgets.QPushButton("Cancel")

        # set the layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(lambdlab)
        hbox.addWidget(self.lambdtext)
        hbox.addWidget(plab)
        hbox.addWidget(self.ptext)
        hbox.addWidget(exeBtn)
        hbox.addWidget(subBtn)
        hbox.addWidget(addBtn)
        hbox.addWidget(cancelBtn)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

        # Connect buttons to callback functions
        exeBtn.clicked.connect(self.compute)
        subBtn.clicked.connect(self.correct)
        addBtn.clicked.connect(self.create)
        cancelBtn.clicked.connect(self.reject)
        self.setWindowTitle('ALS Smoothing tool')

        self.initWidgets()
        self.compute()


    def initWidgets(self):
        """ Initialize the dialog widgets with self.lambd and self.p values.

        :return:
        """
        self.lambdtext.setText(str(self.lambd))
        self.ptext.setText(str(self.p))


    def updatePlot(self):
        """ Update the plotting area.

            Plot 3 curves: y1 = initial data, y2 = smoothed data, y3 = y2 - y1
        :return: nothing
        """
        self.axes.clear()
        self.axes.plot(self.data[0], self.data[1], linestyle='-', color='gray')
        self.axes.plot(self.data[0], self.data[2], linestyle='-', color='blue')
        self.canvas.draw()


    def correct(self):
        """ Callback function when user has clicked on Subtract button.

            The baseline is subtracted from the initial data.

        :return: nothing
        """
        self.parent.copyCurrentWinState(self.pltw)
        self.pltw.blklst[self.blkno][self.ypos] = self.data[1] - self.data[2]
        self.pltw.updatePlot()
        self.pltw.dirty = True
        self.pltw.activecurv = self.cpos
        self.parent.updateUI()
        self.hide()


    def create(self):
        """ Callback function when user has clicked on Add button.

            A new vector containing the baseline is added to the
            initial data block.

        :return: nothing
        """
        self.parent.copyCurrentWinState(self.pltw)
        # add a new vector
        vname = self.pltw.curvelist[self.cpos].name + 'BL'
        (nvec, npt) = np.shape(self.pltw.blklst[self.blkno])
        if self.pltw.pasteVector(self.data[2], self.blkno, vname):
            xname = self.pltw.getVnam(self.blkno, self.xpos)
            xvinfo = vectInfo(self.blkno, self.xpos, xname)
            yvinfo = vectInfo(self.blkno, nvec, vname)
            self.pltw.curvelist.append(curveInfo(vname, xvinfo, yvinfo))
        self.pltw.updatePlot()
        self.pltw.dirty = True
        self.pltw.activecurv = self.cpos
        self.parent.updateUI()
        self.hide()


    def baseline_als(self, y, lambd, p, niter=10):
        """
        Baseline Correction with Asymmetric Least Squares Smoothing
        from: Paul H. C. Eilers and Hans F.M. Boelens (2005)

        There are two parameters: p for asymmetry and lambda for smoothness.
        Both have to be tuned to the data at hand.
        We found that generally (for a signal with positive peaks) a good
        choice is: 10e2 <= lambda <= 10e9 and 0.001 <= p <= 0.1
        When the noise is low use small value for p (0.01).
        In any case one should vary lambda on a grid that is approximately
        linear for log(lambda). Often visual inspection is sufficient to get
        good parameter values.

        :param y: data vector
        :param lambd: smoothness
        :param p: asymmetry
        :param niter: maximum number of iterations
        :return: a vector, of the same size as y, containing the baseline.
        """
        L = y.size
        D = sparse.csc_matrix(np.diff(np.eye(L), 2))
        w = np.ones(L)
        z = w
        for i in range(niter):
            W = sparse.spdiags(w, 0, L, L)
            Z = W + lambd * D.dot(D.transpose())
            z = spsolve(Z, w*y)
            wold = w
            w = p * (y > z) + (1-p) * (y < z)
            if i > 0:
                # check convergence
                dw = np.sum(wold - w)
                if dw == 0.0:
                    break
        return z


    def compute(self):
        """ Apply the ALS smoothing algorithm.

        :return: nothing
        """
        # update parameters with the values of widgets
        lambd = float(str(self.lambdtext.text()))
        p = float(str(self.ptext.text()))
        # check the values
        # compute
        self.data[2] = self.baseline_als(self.data[1], lambd, p)
        # store the values
        self.lambd = lambd
        self.p = p
        self.updatePlot()



#  modelSelectDlg ------------------------------------------------------------

class modelSelectDlg(QtWidgets.QDialog):
    def __init__(self, parent=None, pltw=None):
        """ This class is used to let the used select a model

        :param parent: pyDataVis MainWindow.
        """
        super (modelSelectDlg, self).__init__(parent)

        self.pltw = pltw
        # Curve name
        cnamlst = []
        namelab = QtWidgets.QLabel("Curve name")
        for curv in self.pltw.curvelist:
            cnamlst.append(curv.name)
        self.nameComboBox = QtWidgets.QComboBox(self)
        self.nameComboBox.addItems(cnamlst)
        # Fitting model
        modellab = QtWidgets.QLabel("Fitting model")
        self.modelComboBox = QtWidgets.QComboBox(self)
        self.modelComboBox.addItems(parent.fitmodels)
        # Buttons
        okBtn = QtWidgets.QPushButton("OK")
        cancelBtn = QtWidgets.QPushButton("Cancel")

        # set the layout
        vbox = QtWidgets.QVBoxLayout()
        hbox1 = QtWidgets.QHBoxLayout()
        hbox1.addWidget(namelab)
        hbox1.addWidget(self.nameComboBox)
        hbox2 = QtWidgets.QHBoxLayout()
        hbox2.addWidget(modellab)
        hbox2.addWidget(self.modelComboBox)
        hbox3 = QtWidgets.QHBoxLayout()
        hbox3.addWidget(okBtn)
        hbox3.addWidget(cancelBtn)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)
        self.setLayout(vbox)

        # Connect buttons to callback functions
        okBtn.clicked.connect(self.accept)
        cancelBtn.clicked.connect(self.reject)
        self.setWindowTitle('Model selection')

    def getValues(self):
        cpos = self.nameComboBox.currentIndex()
        modelno = self.modelComboBox.currentIndex()
        return cpos, modelno


#  fitCurveDlg ------------------------------------------------------------

class fitCurveDlg(QtWidgets.QDialog):
    def __init__(self, parent=None, pltw=None, cpos=None, model=None):
        """ Interactive Curve Fitting Tool dialog.

        :param parent: pyDataVis MainWindow.
        :param cpos: it is the curve position in plotWin.curvelist.
        :param model: the fitting model.
        """
        super (fitCurveDlg, self).__init__(parent)

        self.parent = parent
        self.cpos = cpos
        self.model = model
        self.pltw = pltw
        self.blkno = self.pltw.curvelist[cpos].yvinfo.blkpos
        self.xpos = self.pltw.curvelist[cpos].xvinfo.vidx
        self.ypos = self.pltw.curvelist[cpos].yvinfo.vidx
        self.data = np.vstack( (self.pltw.blklst[self.blkno][self.xpos],
                                self.pltw.blklst[self.blkno][self.ypos],
                                self.pltw.blklst[self.blkno][self.ypos],
                                np.zeros(len(self.pltw.blklst[self.blkno][self.xpos]))) )

        self.diffshift = getSpan(self.data[1]) * 0.2
        if self.data[1].min() + self.diffshift < 0.0:
            self.diffshift *= -1.0

        self.initParms()

        # Create the layout
        self.createLayout()
        # Connect buttons to callback functions
        self.exeBtn.clicked.connect(self.compute)
        self.okBtn.clicked.connect(self.validate)
        self.cancelBtn.clicked.connect(self.reject)
        self.setWindowTitle('Curve Fitting tool')

        self.updateParms()
        self.compute()


    def initParms(self):
        """ Initialize the model parameters according to self.model value.

        :return: nothing
        """
        self.parmVal = []
        self.parmName = []
        (nvect, npt) = self.data.shape
        if self.model == 0:
            self.parmVal.append(2.0)
            self.parmName.append('Order')
        if self.model == 1:
            self.parmVal.append(1.0)
            self.parmName.append('A')
            self.parmVal.append(1.0)
            self.parmName.append('B')
        if self.model == 2:
            self.parmVal.append(self.data[1][0])
            self.parmName.append('A')
            self.parmVal.append(self.data[1][npt-1])
            self.parmName.append('B')
        if self.model == 3:
            self.parmVal.append(self.data[1][0])
            self.parmName.append('Ao')
            self.parmVal.append(100.0)
            self.parmName.append('Ea')
        if self.model == 4:
            self.parmVal.append(0.001)
            self.parmName.append('A')
            self.parmVal.append(1.0)
            self.parmName.append('B')
        if self.model == 5:
            self.parmVal.append(0.001)
            self.parmName.append('A')
            self.parmVal.append(0.0)
            self.parmName.append('B')
            self.parmVal.append(1.0)
            self.parmName.append('C')
        if self.model == 6:
            self.parmVal.append(self.data[0][0])
            self.parmName.append('xo')
            self.parmVal.append(self.data[1][0])
            self.parmName.append('yo')
            yspan = getSpan(self.data[1])
            if self.data[1][0] > 0.0:
                v = self.data[1][0] + yspan/2.0
            else:
                v = self.data[1][npt-1] + yspan/2.0
            self.parmVal.append(v)
            self.parmName.append('H')
            if self.data[1][0] > self.data[1][npt-1]:
                self.parmVal.append(-1.0)
            else:
                self.parmVal.append(1.0)
            self.parmName.append('S')


    def createLayout(self):
        """ Create the dialog layout according to the number of parameters.

        :return:
        """
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.canvas.setFocus()
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        self.axes = self.fig.add_subplot(111)
        # Log window
        self.log = QtWidgets.QTextEdit(self)
        self.log.setCurrentFont(self.parent.txteditfont)
        self.log.setFixedHeight(90)
        self.log.setReadOnly(True)
        # Parameters
        p1lab = QtWidgets.QLabel(self.parmName[0])
        self.p1text = QtWidgets.QLineEdit(self)
        regex = QRegExp("-?[0-9]+.?[0-9]{,5}")
        validator = QtGui.QRegExpValidator(regex, self.p1text)
        self.p1text.setValidator(validator)
        if len(self.parmName) > 1:
            p2lab = QtWidgets.QLabel(self.parmName[1])
            self.p2text = QtWidgets.QLineEdit(self)
            validator = QtGui.QRegExpValidator(regex, self.p2text)
            self.p2text.setValidator(validator)
        if len(self.parmName) > 2:
            p3lab = QtWidgets.QLabel(self.parmName[2])
            self.p3text = QtWidgets.QLineEdit(self)
            validator = QtGui.QRegExpValidator(regex, self.p3text)
            self.p3text.setValidator(validator)
        if len(self.parmName) > 3:
            p4lab = QtWidgets.QLabel(self.parmName[3])
            self.p4text = QtWidgets.QLineEdit(self)
            validator = QtGui.QRegExpValidator(regex, self.p4text)
            self.p4text.setValidator(validator)
        # Buttons
        self.exeBtn = QtWidgets.QPushButton("Compute")
        self.okBtn = QtWidgets.QPushButton("OK")
        self.cancelBtn = QtWidgets.QPushButton("Cancel")

        # set the layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.log)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(p1lab)
        hbox.addWidget(self.p1text)
        if len(self.parmName) > 1:
            hbox.addWidget(p2lab)
            hbox.addWidget(self.p2text)
        if len(self.parmName) > 2:
           hbox.addWidget(p3lab)
           hbox.addWidget(self.p3text)
        if len(self.parmName) > 3:
           hbox.addWidget(p4lab)
           hbox.addWidget(self.p4text)
        hbox.addWidget(self.exeBtn)
        hbox.addWidget(self.okBtn)
        hbox.addWidget(self.cancelBtn)
        vbox.addLayout(hbox)
        self.setLayout(vbox)


    def compute(self):
        """ Apply the fitting algorithm according to self.model value.

        :return: nothing
        """
        # update parameters with the values of widgets
        self.parmVal[0] = float(str(self.p1text.text()))
        if len(self.parmName) > 1:
            self.parmVal[1] = float(str(self.p2text.text()))
        if len(self.parmName) > 2:
            self.parmVal[2] = float(str(self.p3text.text()))
        if len(self.parmName) > 3:
            self.parmVal[3] = float(str(self.p4text.text()))

        if self.model == 0:
            # Polynomial fit
            order = int(self.parmVal[0])
            pcoef = np.polyfit(self.data[0], self.data[1], order)
            Yfit = np.polyval(pcoef, self.data[0])
            # compute the root mean square error (RMSE)
            err = np.sqrt(sum((Yfit-self.data[1])**2) / len(self.data[1]))
            msg = 'Least squares polynomial fit - '
            msg += 'Polynom order = {}\n'.format(order)
            msg += 'c{0} = {1}\n'.format(order, pcoef[0])
            for i in range(order):
                msg += 'c{0} = {1}\n'.format(order-1, pcoef[i+1])
            msg += 'RMSE = {0:g}\n'.format(err)
            # compute 1st derivative
            pfit = np.poly1d(pcoef)
            pdercoef = np.polyder(pcoef, 1)
            pder = np.poly1d(pdercoef)
            # print roots
            st = "Root(s) of the 1st derivative = {0}\n"
            msg += st.format(np.array2string(pder.r))

        elif self.model == 1:
            # Fitting with exponential equation A*exp(B*x)
            from scipy.optimize import leastsq
            # initial guesses
            p0 = [self.parmVal[0], self.parmVal[1]]
            pbest1 = leastsq(self.residuals_Exp, p0, args=(self.data[1], self.data[0]))
            Yfit = self.Exp(self.data[0], pbest1[0])
            Res = self.residuals_Exp(pbest1[0], self.data[1], self.data[0])
            # compute the root mean square error (RMSE)
            err = np.sqrt(np.sum(np.square(Res)) / len(self.data[1]))
            msg = 'Fitting with exponential equation: A * exp(B * x)\n'
            msg += '[A, B] = {0}\n'.format(str(pbest1[0]))
            msg += 'RMSE = {0:g}\n\n'.format(err)
            self.parmVal = pbest1[0]

        elif self.model == 2:
            # Fitting with logarithm equation A*Ln(x)+B
            from scipy.optimize import leastsq
            # initial guesses
            p0 = [self.parmVal[0], self.parmVal[1]]
            pbest1 = leastsq(self.residuals_Log, p0, args=(self.data[1], self.data[0]))
            Yfit = self.Log(self.data[0], pbest1[0])
            Res = self.residuals_Log(pbest1[0], self.data[1], self.data[0])
            # compute the root mean square error (RMSE)
            err = np.sqrt(np.sum(np.square(Res)) / len(self.data[1]))
            msg = 'Fitting with logarithm equation: A * Ln(x) + B\n'
            msg += '[A, B] = {0}\n'.format(str(pbest1[0]))
            msg += 'RMSE = {0:g}\n\n'.format(err)
            self.parmVal = pbest1[0]

        elif self.model == 3:
            # Fitting with Arrhenius equation A*exp(-(E/(R*(x+273))))
            from scipy.optimize import leastsq
            # initial guesses
            p0 = [self.parmVal[0], self.parmVal[1]]
            pbest1 = leastsq(self.residuals_Arr, p0, args=(self.data[1], self.data[0]))
            Yfit = self.Arr(self.data[0], pbest1[0])
            Res = self.residuals_Arr(pbest1[0], self.data[1], self.data[0])
            # compute the root mean square error (RMSE)
            err = np.sqrt(np.sum(np.square(Res)) / len(self.data[1]))
            msg = 'Fitting with Arrhenius equation: A * exp(-(E/(R * (x + 273))))\n'
            msg += '[A, E] = {0}\n'.format(str(pbest1[0]))
            msg += 'RMSE = {0:g}\n\n'.format(err)
            self.parmVal = pbest1[0]

        elif self.model == 4:
            # Fitting data with Power model
            from scipy.optimize import leastsq
            # initial guesses
            p0 = [self.parmVal[0], self.parmVal[1]]
            pbest1 = leastsq(self.residuals_PL, p0, args=(self.data[1], self.data[0]))
            Yfit = self.PowerLaw(self.data[0], pbest1[0])
            Res = self.residuals_PL(pbest1[0], self.data[1], self.data[0])
            # compute the root mean square error (RMSE)
            err = np.sqrt(np.sum(np.square(Res)) / len(self.data[1]))
            msg = 'Fitting with Power model: A * x^B\n'
            msg += '[A, B] = {0}\n'.format(str(pbest1[0]))
            msg += 'RMSE = {0:g}\n\n'.format(err)
            self.parmVal = pbest1[0]

        elif self.model == 5:
            # Fitting Rheo data with Herschel-Bulkley model
            from scipy.optimize import leastsq
            # initial guesses
            p0 = [self.parmVal[0], self.parmVal[1], self.parmVal[2]]
            pbest1 = leastsq(self.residuals_HB, p0, args=(self.data[1], self.data[0]))
            Yfit = self.HerschelBulkley(self.data[0], pbest1[0])
            Res = self.residuals_HB(pbest1[0], self.data[1], self.data[0])
            # compute the root mean square error (RMSE)
            err = np.sqrt(np.sum(np.square(Res)) / len(self.data[1]))
            msg = 'Fitting with Herschel-Bulkley model: A + B * x^C\n'
            msg += '[A, B, C] = {0}\n'.format(str(pbest1[0]))
            msg += 'RMSE = {0:g}\n\n'.format(err)
            self.parmVal = pbest1[0]

        elif self.model == 6:
            # Fitting with sigmoid S+H/(1+exp(-lambda*x)
            from scipy.optimize import leastsq
            # initial guesses
            p0 = [self.parmVal[0], self.parmVal[1], self.parmVal[2], self.parmVal[3]]
            pbest1 = leastsq(self.residuals_Sigm, p0, args=(self.data[1], self.data[0]))
            Yfit = self.Sigm(self.data[0], pbest1[0])
            Res = self.residuals_Sigm(pbest1[0], self.data[1], self.data[0])
            # compute the root mean square error (RMSE)
            err = np.sqrt(np.sum(np.square(Res)) / len(self.data[1]))
            msg = 'Fitting with sigmoid equation: yo + H /(1 + exp(S * (xo - x))\n'
            msg += '[xo, yo, H, S] = {0}\n'.format(str(pbest1[0]))
            msg += 'RMSE = {0:g}\n\n'.format(err)
            self.parmVal = pbest1[0]

        else:
            msg = 'Unknown model'
            Yfit = self.data[1]

        # Show results in log windows
        self.log.setText(msg)
        # write current date and time from now variable
        msg = "#\n#%s\n" % datetime.datetime.now() + msg
        self.saveToLogFile(msg)
        self.data[2] = Yfit
        self.data[3] = self.data[2] - self.data[1] - self.diffshift

        self.updatePlot()
        self.updateParms()



    def Arr(self, x, p):
        """ Arrhenius function.

        :param x: X vector (Temperature)
        :param p: the function parameters p[0] = A and p[1] = E.
        :return: a vector with the function values.
        """
        R=8.3144
        return(p[0]*np.exp(-(p[1]/(R*(x+273)))))

    def residuals_Arr(self, p, data, x):
        """ Compute the residuals between the Arrhenius function and the data.

        :param p: the parameters, p[0] = A and p[1] = E.
        :param data: the data vector (Y).
        :param x: the X vector.
        :return: a vector with the residuals
        """
        err = data - self.Arr(x,p)
        return err


    def Exp(self, x, p):
        """ Exponential function.

        :param x: X vector
        :param p: the parameters, p[0] = A and p[1] = B.
        :return: a vector with the function values.
        """
        return(p[0]*np.exp(p[1]*x))

    def residuals_Exp(self, p, data, x):
        """ Compute the residuals between the Exponential function and the data.

        :param p: the parameters, p[0] = A and p[1] = B.
        :param data: the data vector (Y).
        :param x: the X vector.
        :return: a vector with the residuals
        """
        err = data - self.Exp(x,p)
        return err


    def Log(self, x, p):
        """ Logarithm function.

        :param x: X vector
        :param p: the parameters, p[0] = A and p[1] = B.
        :return: a vector with the function values.
        """
        return(p[0]*np.log(x)+p[1])

    def residuals_Log(self, p, data, x):
        """ Compute the residuals between the Logarithm function and the data.

        :param p: the parameters, p[0] = A and p[1] = B.
        :param data: the data vector (Y).
        :param x: the X vector.
        :return: a vector with the residuals
        """
        err = data - self.Log(x,p)
        return err


    def PowerLaw(self, x, p):
        """ Power law function.

        :param x: X vector
        :param p: the parameters, p[0] = A and p[1] = B.
        :return: a vector with the function values.
        """
        return(p[0]*x**p[1])

    def residuals_PL(self, p, data, x):
        """ Compute the residuals between the Power law function and the data.

        :param p: the parameters, p[0] = A and p[1] = B.
        :param data: the data vector (Y).
        :param x: the X vector.
        :return: a vector with the residuals
        """
        err = data - self.PowerLaw(x,p)
        return err


    def HerschelBulkley(self, x, p):
        """ Herschel Bulkey function.

        :param x: X vector
        :param p: the parameters, p[0] = A, p[1] = B and p[2] = C.
        :return: a vector with the function values.
        """
        return(p[0] + p[1]*x**p[2])

    def residuals_HB(self, p, data, x):
        """ Compute the residuals between the H-B function and the data.

        :param p: the parameters, p[0] = A, p[1] = B and p[2] = C.
        :param data: the data vector (Y).
        :param x: the X vector.
        :return: a vector with the residuals
        """
        err = data - self.HerschelBulkley(x,p)
        return err


    def Sigm(self, x, p):
        """ Sigmoid function.

        :param x: X vector
        :param p: the parameters, p[0]= x0, p[1]= y0, p[2]= H, p[3]= S.
        :return: a vector with the function values.
        """
        return(p[1] + p[2]/(1 + np.exp(p[3] * (p[0] - x))))

    def residuals_Sigm(self, p, data, x):
        """ Compute the residuals between the sigmoid function and the data.

        :param p: the parameters, p[0]= x0, p[1]= y0, p[2]= H, p[3]= S.
        :param data: the data vector (Y).
        :param x: the X vector.
        :return: a vector with the residuals
        """
        err = data - self.Sigm(x,p)
        return err


    def saveToLogFile(self, msg):
        """ Save 'msg' in the log file

        :param msg: string containing the message 'msg'.
        :return: nothing
        """
        fo = open("logfile.txt", 'a')
        fo.write(msg)
        fo.close()


    def updatePlot(self):
        """ Update the plotting area.

            Plot 3 curves: y1 = initial data, y2 = smoothed data, y3 = y2 - y1
        :return: nothing
        """
        self.axes.clear()
        self.axes.plot(self.data[0], self.data[1], linestyle='-', color='gray')
        self.axes.plot(self.data[0], self.data[2], linestyle='-', color='blue')
        self.axes.plot(self.data[0], self.data[3], linestyle='-', color='darkgreen')
        self.canvas.draw()



    def updateParms(self):
        """ Update the text widgets with the values of parameters.

        :return: nothing
        """
        self.p1text.setText("{0:g}".format(self.parmVal[0]))
        if len(self.parmVal) > 1:
            self.p2text.setText("{0:g}".format(self.parmVal[1]))
        if len(self.parmVal) > 2:
            self.p3text.setText("{0:g}".format(self.parmVal[2]))
        if len(self.parmVal) > 3:
            self.p4text.setText("{0:g}".format(self.parmVal[3]))


    def validate(self):
        """ Callback function when user has clicked on OK button.

            The original data is replaced by the vector with fitted data,
         :return: nothing
         """
        self.pltw.blklst[self.blkno][self.ypos] = self.data[2]
        self.pltw.updatePlot()
        self.pltw.dirty = True
        self.parent.fitmodel = self.model
        self.pltw.activecurv = self.cpos
        self.parent.updateUI()
        self.hide()


#  pkfitDlg ------------------------------------------------------------

class pkfitDlg(QtWidgets.QDialog):
    def __init__(self, parent=None, pltw=None, cpos=None, stguess=None):
        """ Interactive Peak Fitting Tool dialog.

         :param parent: pyDataVis MainWindow.
         :param cpos: it is the curve position in plotWin.curvelist.
         :param stguess: string containing the first estimate of
                         the peak parameters.
         """
        super(pkfitDlg, self).__init__(parent)

        self.parent = parent
        self.title = 'Peak Fitting tool'
        self.pltw = pltw
        self.cpos = cpos
        self.stguess = stguess
        self.maxparm = 5
        self.first = True
        self.npeaks = 0
        self.blkno = self.pltw.curvelist[cpos].yvinfo.blkpos
        self.xpos = self.pltw.curvelist[cpos].xvinfo.vidx
        self.ypos = self.pltw.curvelist[cpos].yvinfo.vidx
        self.data = np.vstack((self.pltw.blklst[self.blkno][self.xpos],
                               self.pltw.blklst[self.blkno][self.ypos],
                               self.pltw.blklst[self.blkno][self.ypos],
                               np.zeros(len(self.pltw.blklst[self.blkno][self.xpos]))))
        (self.nvect, self.npt) = self.data.shape
        self.diffshift = getSpan(self.data[1]) * 0.2
        if self.data[1].min() + self.diffshift < 0.0:
            self.diffshift *= -1.0

        if stguess is not None:
            self.stguess = stguess.replace('\n', ',')
            self.guessToParms(self.stguess)

        # Create the layout
        self.createLayout()
        # Connect buttons to callback functions
        self.exeBtn.clicked.connect(self.compute)
        self.okBtn.clicked.connect(self.validate)
        self.cancelBtn.clicked.connect(self.reject)
        self.setWindowTitle(self.title)

        self.updateParmsEdit()
        self.compute()


    def createLayout(self):
        """ Create the layout of the Peak Fitting dialog.

        :return: nothing
        """
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.canvas.setFocus()
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        self.axes = self.fig.add_subplot(111)
        # Log window
        self.log = QtWidgets.QTextEdit(self)
        self.log.setCurrentFont(self.parent.txteditfont)
        self.log.setFixedHeight(200)
        self.log.setReadOnly(True)
        # Parameters
        plab = QtWidgets.QLabel("Peak parameters (type, pos, amp, FWHM, a, b)")
        self.ptext = QtWidgets.QTextEdit(self)
        self.ptext.setCurrentFont(self.parent.txteditfont)
        # Buttons
        self.exeBtn = QtWidgets.QPushButton("Compute")
        self.okBtn = QtWidgets.QPushButton("OK")
        self.cancelBtn = QtWidgets.QPushButton("Cancel")

        # set the layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.log)
        vbox.addWidget(plab)
        vbox.addWidget(self.ptext)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.exeBtn)
        hbox.addWidget(self.okBtn)
        hbox.addWidget(self.cancelBtn)
        vbox.addLayout(hbox)
        self.setLayout(vbox)


    def checkUserInput(self, stguess):
        """ Check the user input.

        :param stguess: a string containing each peak parameters:
                        type, pos, amp, width, a, b
                        separated, by comma, one line per peak
        :return: True if no error is detected, False otherwise.
        """
        lines = stguess.splitlines()
        err = ""
        for l, line in enumerate(lines):
            items = line.split(',')
            np = len(items)
            if np != 4 and np != 6:
                err = "Wrong number of parameters"
            else:
                for p in range(0, np):
                    val = items[p].strip()
                    if p == 0:
                        if not val in ['G', 'L', 'P', 'AG', 'AL', 'AP']:
                            err = "Unknown peak type"
                        else:
                            pktyp = val
                    else:
                        if not isNumber(val):
                            err = "Parameter {0} in not numeric".format(p+1)
                        else:
                            if float(val) < 0.0:
                                if not(pktyp[0] == 'A' and p == 4):
                                    err = "Parameter {0} is negative".format(p+1)
                    if err:
                        break
            if err:
                errmsg = "Error in peak {0}:\n{1}".format(l+1, err)
                QtWidgets.QMessageBox.warning(self, self.title, errmsg)
                return False
        return True


    def guessToParms(self, stguess):
        """ Use stguess to update the peak parameters

        :param stguess: string containing the peak parameters separated by comma.
        :return: None
        """
        self.peakTyp = []
        self.parmVal = []
        self.parmName = []
        items = str(stguess).split(',')
        items = [item for item in items if item]   # delete empty elements
        if self.first:
            # The first time peak is defined by 4 parameters:
            # type, xc, Amp, width
            n = 4
            self.first = False
        else:
            # Subsequently each peak is defined by 6 parameters:
            # type, xc, Amp, width, a, b
            n = 6
        ntot = len(items)
        self.npeaks = int(ntot/n)
        if self.npeaks == 0:
            return
        for i in range(0, ntot, n):
            stpkno = str((i/n)+1)
            peakTyp = items[i].strip()
            self.peakTyp.append(peakTyp)
            self.parmVal.append(float(items[i+1]))
            self.parmName.append('xm'+stpkno)
            self.parmVal.append(float(items[i+2]))
            self.parmName.append('amp'+stpkno)
            self.parmVal.append(float(items[i+3]))
            self.parmName.append('wid'+stpkno)
            # Add two extra parameters for Pseudo-Voigt and asymmetric peaks
            if peakTyp == 'P' or peakTyp == 'AP':
                self.parmVal.append(0.5)
                self.parmName.append('f' + stpkno)
            else:
                self.parmVal.append(0.0)
                self.parmName.append('a'+stpkno)
            self.parmVal.append(0.0)
            if peakTyp == 'AP':
                self.parmName.append('a'+stpkno)
            else:
                self.parmName.append('b'+stpkno)


    def fitfunc(self, x, p):
        """ Return a vector containing the sum of the peak functions.

        :param x: X vector
        :param p: the list of each peak parameters.
        :return: The sum vector.
        """
        S = np.zeros(self.npt)
        for i in range(0, len(p), self.maxparm):
            ptyp = self.peakTyp[int(i/self.maxparm)]
            xm = p[i]
            amp = p[i+1]
            w = p[i+2]
            a = p[i+3]
            b = p[i+4]
            if ptyp == 'G':
                # peak type = Gaussian
                S = S + self.gauss(x, xm, amp, w)
            elif ptyp == 'L':
                # peak type = Lorentzian
                S = S + self.lorentz(x, xm, amp, w)
            elif ptyp == 'P':
                # peak type = Pseudo-Voigt
                S = S + self.psVoigt(x, xm, amp, w, a)
            elif ptyp == 'AG':
                # peak type = Asymmetric Gaussian
                S = S + self.agauss(x, xm, amp, w, a)
            elif ptyp == 'AL':
                # peak type = Asymmetric Lorentzian
                S = S + self.alorentz(x, xm, amp, w, a)
            elif ptyp == 'AP':
                # peak type = Asymmetric Pseudo-Voigt
                S = S + self.aPsVoigt(x, xm, amp, w, a, b)
        return S


    def gauss(self, x, xm, amp, w):
        """ Compute the Gaussian peak profile.

        :param x:  X vector.
        :param xm: Position of the peak maximum.
        :param amp: Peak amplitude
        :param w: Peak Full Width at Half Maximum.
        :return: a vector with the peak profile.
        """
        S = np.zeros(self.npt)
        S = S + amp * np.exp(-((x - xm) / w) ** 2)
        return S

    def lorentz(self, x, xm, amp, w):
        """ Compute the Lorentzian peak profile.

        :param x:  X vector.
        :param xm: Position of the peak maximum.
        :param amp: Peak amplitude
        :param w: Peak Full Width at Half Maximum.
        :return: a vector with the peak profile.
        """
        S = np.zeros(self.npt)
        S = S + amp / (1 + ((x - xm) / (w / 2)) ** 2)
        return S

    def psVoigt(self, x, xm, amp, w, f):
        """ Compute the pseudo-Voigt peak profile.

        :param x:  X vector.
        :param xm: Position of the peak maximum.
        :param amp: Peak amplitude
        :param w: Peak Full Width at Half Maximum.
        :param f: fraction of Lorentzian.
        :return: a vector with the peak profile.
        """
        S = np.zeros(self.npt)
        S = S + f * self.lorentz(x, xm, amp, w) + (1-f) * self.gauss(x, xm, amp, w)
        return S

    def agauss(self, x, xm, amp, w, a):
        """ Compute the asymetric Gaussian peak profile.

        :param x:  X vector.
        :param xm: Position of the peak maximum.
        :param amp: Peak amplitude
        :param w: Peak Full Width at Half Maximum.
        :param a: Asymmetry parameter.
        :return: a vector with the peak profile.
        """
        # w(x) = 2 * w / (1 + np.exp(a * (x - xm)))
        S = np.zeros(self.npt)
        S = S + amp * np.exp(-((x - xm) / (2 * w / (1 + np.exp(a * (x - xm))))) ** 2)
        return S

    def alorentz(self, x, xm, amp, w, a):
        """ Compute the asymetric Lorentzian peak profile.

        :param x:  X vector.
        :param xm: Position of the peak maximum.
        :param amp: Peak amplitude
        :param w: Peak Full Width at Half Maximum.
        :param a: Asymmetry parameter.
        :return: a vector with the peak profile.
        """
        # w(x) = 2 * w / (1 + np.exp(a * (x - xm)))
        S = np.zeros(self.npt)
        S = S + amp / (1 + ((x - xm) / ((2 * w / (1 + np.exp(a * (x - xm)))) / 2)) ** 2)
        return S

    def aPsVoigt(self, x, xm, amp, w, f, a):
        """ Compute the asymetric pseudo-Voigt peak profile.

        :param x:  X vector.
        :param xm: Position of the peak maximum.
        :param amp: Peak amplitude
        :param w: Peak Full Width at Half Maximum.
        :param a: Asymmetry parameter.
        :param f: fraction of Lorentzian.
        :return: a vector with the peak profile.
        """
        S = np.zeros(self.npt)
        S = S + f * self.alorentz(x, xm, amp, w, a) + (1-f) * self.agauss(x, xm, amp, w, a)
        return S


    def residuals(self, p, data, x):
        """ Compute the residuals between the peak function and the data.

        :param p: the peak parameters.
        :param data: the data vector (Y).
        :param x: the X vector.
        :return: a vector with the residuals
        """
        err = data - self.fitfunc(x,p)
        return err


    def compute(self):
        """ Launch the peak fitting process.

        :return: nothing
        """
        # update parameters with the values of widgets
        initguess = str(self.ptext.toPlainText())
        if not self.checkUserInput(initguess):
            return
        stguess = initguess.replace('\n', ',')
        # update self.parmVal
        self.guessToParms(stguess)
        self.parent.app.setOverrideCursor(Qt.WaitCursor)
        pbest1 = leastsq(self.residuals, self.parmVal, args=(self.data[1], self.data[0]))
        self.parent.app.restoreOverrideCursor()
        Yfit = self.fitfunc(self.data[0], pbest1[0])
        Res = self.residuals(pbest1[0], self.data[1], self.data[0])
        RMSE = np.sqrt(np.sum(np.square(Res)) / len(self.data[1]))
        msg = "Initial guess : \n{0}\n".format(initguess)
        msg += "Number of peaks = {0:d}\n".format(self.npeaks)
        msg += 'Fitting results:\n'
        msg += '[xm, amp, fwhm, a, b] = \n{0}\n'.format(str(pbest1[0]))
        msg += 'RMSE = {0:g}\n\n'.format(RMSE)
        self.parmVal = pbest1[0]

        # Show results in log windows
        self.log.setText(msg)
        self.saveToLogFile(msg)
        self.data[2] = Yfit
        self.data[3] = self.data[2] - self.data[1] - self.diffshift

        self.updatePlot()
        self.updateParmsEdit()


    def saveToLogFile(self, msg):
        """ Save the message 'msg' in the log file

        :param msg: A string containing the message
        :return: nothing
        """
        fo = open("logfile.txt", 'a')
        fo.write(msg)
        fo.close()


    def updatePlot(self):
        """ Udate the plotting area.

        :return: nothing.
        """
        self.axes.clear()
        self.axes.plot(self.data[0], self.data[1], linestyle='-', color='gray')
        self.axes.plot(self.data[0], self.data[2], linestyle='-', color='blue')
        self.axes.plot(self.data[0], self.data[3], linestyle='-', color='darkgreen')
        self.canvas.draw()


    def updateParmsEdit(self):
        """ Use the peak parameters values to update the text editor

        :return: the text in self.ptext
        """
        stparms = ""
        n = self.maxparm
        nv = len(self.parmVal)
        for i, parm in enumerate(self.parmVal):
            if not i % n:
                # new peak parms
                stparms += self.peakTyp[int(i / n)] + ', '
            parm = round_to_n(parm, 4)
            stparms += str(parm)
            if i < nv - 1:
                if (i+1) % n:
                    stparms += ', '
                else:
                    stparms += '\n'
        self.ptext.setText(stparms)
        return stparms


    def validate(self):
        """ Callback function when user has clicked on OK button.

            The original data is replaced by the vector with fitted data,

        :return: nothing
        """
        vnames = []
        vnames.append(self.pltw.vectInfolst[self.blkno][0].name)
        vnames.append(self.pltw.vectInfolst[self.blkno][1].name)
        vnames.append("pksum")

        savename = "peakFit.txt"
        txt = "Number of peaks = {0}\n".format(self.npeaks)
        txt += "Fitting results:\n"
        txt += "pktyp\t xm\t amp\t width\t area\n"

        newset = np.vstack((self.pltw.blklst[self.blkno], self.data[2]))
        for i in range(0, len(self.parmVal), self.maxparm):
            pkno = int(i/self.maxparm)
            ptyp = self.peakTyp[pkno]
            xm = self.parmVal[i]
            amp = self.parmVal[i+1]
            w = self.parmVal[i+2]
            a = self.parmVal[i+3]
            b = self.parmVal[i+4]
            area = 0.0
            if ptyp == 'G':
                S = self.gauss(self.data[0], xm, amp, w)
            elif ptyp == 'L':
                S = self.lorentz(self.data[0], xm, amp, w)
            elif ptyp == 'P':
                S = self.psVoigt(self.data[0], xm, amp, w, a)
            elif ptyp == 'AG':
                S = self.agauss(self.data[0], xm, amp, w, a)
            elif ptyp == 'AL':
                S = self.alorentz(self.data[0], xm, amp, w, a)
            elif ptyp == 'AP':
                S = self.aPsVoigt(self.data[0], xm, amp, w, a, b)
            newset = np.vstack((newset, S))
            area = calcArea(self.data[0], S, True)
            area = round_to_n(area, 4)
            xm = round_to_n(xm, 4)
            amp = round_to_n(amp, 4)
            w = round_to_n(w, 4)
            a = round_to_n(a, 4)
            b = round_to_n(b, 4)
            vnames.append("pk{0}".format(pkno+1))
            txt += "{0}\t {1}\t {2} \t {3}\t {4}\n".format(ptyp, xm, amp, w, area)

        # Save data and peaks in a text file
        stnam = "\n{0}".format("\t".join(vnames))
        txt += stnam
        np.savetxt(savename, np.transpose(newset), fmt='%+1.4E', header=txt)
        # load the converted file
        self.parent.loadFile(savename)
        self.hide()



#  interpolDlg ------------------------------------------------------------

# blk1 = original data
# blk2 = interpolated data

class interpolDlg(QtWidgets.QDialog):
    def __init__(self, parent=None, pltw=None, parmlist=None):
        """ Interactive Interpolation Tool dialog.

         :param parent: pyDataVis MainWindow.
         :param parmlist: List of the 3 parameters used, dx, s, k.
         """
        super (interpolDlg, self).__init__(parent)

        self.parent = parent
        self.pltw = pltw
        self.blkno = parmlist[0][1]
        self.dx = parmlist[1][1]
        self.s = parmlist[2][1]
        self.k = parmlist[3][1]
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.canvas.setFocus()
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        self.axes = self.fig.add_subplot(111)
        self.col = ['b', 'g', 'r']
        # Initialize the data according to self.blkno.
        self.initDataParms()
        # Build the curve list belonging to the current data block
        self.updateCurveList()
        # Set the layout
        # Data block number
        blknolab = QtWidgets.QLabel(parmlist[0][0])
        self.blknoSpinBox = QtWidgets.QSpinBox(self)
        self.blknoSpinBox.setMaximum(len(self.pltw.blklst))
        self.blknoSpinBox.setMinimum(1)
        # dx
        dxlab = QtWidgets.QLabel(parmlist[1][0])
        str = "{0:g}".format(parmlist[1][1])
        self.dxtext = QtWidgets.QLineEdit(str)
        regex = QRegExp("[0-9]+.?[0-9]{,6}")
        validator = QtGui.QRegExpValidator(regex, self.dxtext)
        self.dxtext.setValidator(validator)
        # s
        if len(parmlist) > 2:
            slab = QtWidgets.QLabel(parmlist[2][0])
            str = "{0:g}".format(parmlist[2][1])
            self.stext = QtWidgets.QLineEdit(str)
            validator = QtGui.QRegExpValidator(regex, self.stext)
            self.stext.setValidator(validator)
        # k
        if len(parmlist) > 3:
            klab = QtWidgets.QLabel(parmlist[3][0])
            self.kComboBox = QtWidgets.QComboBox(self)
            klist = ['3', '5', '7']    # list of valid k values
            self.kComboBox.addItems(klist)

        # Buttons
        exeBtn = QtWidgets.QPushButton("Compute")
        okBtn = QtWidgets.QPushButton("OK")
        cancelBtn = QtWidgets.QPushButton("Cancel")

        # set the layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)

        hbox1 = QtWidgets.QHBoxLayout()
        hbox1.addWidget(blknolab)
        hbox1.addWidget(self.blknoSpinBox)
        hbox1.addSpacing(20)

        hbox2 = QtWidgets.QHBoxLayout()
        hbox2.addWidget(dxlab)
        hbox2.addWidget(self.dxtext)
        hbox2.addSpacing(20)

        hbox3 = QtWidgets.QHBoxLayout()
        hbox3.addWidget(slab)
        hbox3.addWidget(self.stext)
        hbox3.addSpacing(20)

        hbox4 = QtWidgets.QHBoxLayout()
        hbox4.addWidget(klab)
        hbox4.addWidget(self.kComboBox)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addLayout(hbox1)
        hbox.addLayout(hbox2)
        hbox.addLayout(hbox3)
        hbox.addLayout(hbox4)

        hbox5 = QtWidgets.QHBoxLayout()
        hbox5.addWidget(exeBtn)
        hbox5.addWidget(okBtn)
        hbox5.addWidget(cancelBtn)

        vbox.addLayout(hbox)
        vbox.addLayout(hbox5)
        self.setLayout(vbox)

        # Connect to callback functions
        self.blknoSpinBox.valueChanged.connect(self.updateBlock)
        exeBtn.clicked.connect(self.compute)
        okBtn.clicked.connect(self.validate)
        cancelBtn.clicked.connect(self.reject)
        self.setWindowTitle('Interpolation tool')
        # Init widgets
        self.blknoSpinBox.setValue(parmlist[0][1])
        self.compute()


    def initDataParms(self):
        """ Initialize the data after a change of data block number.

        :return: nothing
        """
        self.xpos = self.pltw.curvelist[self.blkno].xvinfo.vidx
        self.data = self.pltw.blklst[self.blkno]     # original data block
        self.idata = None                            # interpolated data
        (self.nvec, self.npt) = self.data.shape
        self.xmin = (self.data[self.xpos]).min()
        self.xmax = (self.data[self.xpos]).max()
        self.xspan = self.xmax - self.xmin


    def updateCurveList(self):
        """ Build the curve list belonging to the current data block.

            Only 3 curves are kept
        :return: nothing
        """
        self.curvelist = []
        for i, cinfo in enumerate(self.pltw.curvelist):
            if cinfo.yvinfo.blkpos == self.blkno:
                self.curvelist.append(cinfo)
                if i > 2:
                    break


    def updateBlock(self):
        """ Callback function when the user change the data block number.

        :return: nothing
        """
        self.blkno = self.blknoSpinBox.value() - 1
        self.initDataParms()
        self.updateCurveList()
        self.compute()


    def compute(self):
        """ Launch the interpolation process.

        :return: nothing
        """
        # Get & check user input values
        dx = float(str(self.dxtext.text()))
        s = float(str(self.stext.text()))
        k = int(str(self.kComboBox.currentText()))
        npt = int(self.xspan / dx + 1)
        errmsg = None
        if npt < 5:
            errmsg = 'dx too large !'
        elif npt > 10000:
            errmsg = u'dx too small !'
        else:
            if s < 0:
                errmsg = 's should be positive !'
            else:
                if k not in [1,3,5]:
                    errmsg = 'k should be 1, 3 or 5 !'
        if errmsg is not None:
            QtWidgets.QMessageBox.warning(self, "Incorrect input values", errmsg)
            return

        idata = np.zeros( (self.nvec, npt) )
        idata[self.xpos] = np.linspace(self.xmin, self.xmax, npt)
        for i in range(self.nvec):
            if i != self.xpos:
                try:
                    tck = interpolate.splrep(self.data[self.xpos], self.data[i],
                                             s=self.s, k=self.k)
                    idata[i] = interpolate.splev(idata[self.xpos], tck)
                    if np.isnan(np.sum(idata[i])):
                        errmsg = "Check that all X are different"
                except (ValueError) as err:
                    errmsg = 'splrep error : ' + str(err)
        if errmsg is not None:
            QtWidgets.QMessageBox.warning(self, "Interpolation", errmsg)
            self.idata = None
        else:
            self.idata = idata
            self.updatePlot()


    def updatePlot(self):
        """ Udate the plotting area.

        :return: nothing.
        """
        self.axes.clear()
        nc = len(self.curvelist)
        xpos = self.curvelist[0].xvinfo.vidx
        for i in range(nc):
            ypos = self.curvelist[i].yvinfo.vidx
            self.axes.plot(self.data[xpos],
                           self.data[ypos], self.col[i])
            if self.idata is not None:
                self.axes.plot(self.idata[xpos],
                               self.idata[ypos], self.col[i]+'.')
        self.canvas.draw()


    def validate(self):
        """ Callback function when user has clicked on OK button.

            The original data is replaced by the vector with interpolated data,

        :return: nothing
        """
        if self.idata is not None:
            self.pltw.blklst[self.blkno] = self.idata
            self.pltw.dirty = True
            self.pltw.updatePlot()
            self.parent.updateUI()
        self.hide()



# baselineDlg --------------------------------------------------------------

# y1 = original data
# y2 = corrected data


class baselineDlg(QtWidgets.QDialog):
    def __init__(self, parent=None, pltw=None, cpos=None):
        """ Interactive Baseline Tool dialog.

         :param parent: pyDataVis MainWindow.
         :param cpos: it is the curve position in plotWin.curvelist.
         """
        super (baselineDlg, self).__init__(parent)

        self.parent = parent
        self.pltw = pltw
        self.cpos = cpos
        self.blkno = self.pltw.curvelist[cpos].yvinfo.blkpos
        self.xpos = self.pltw.curvelist[cpos].xvinfo.vidx
        self.ypos = self.pltw.curvelist[cpos].yvinfo.vidx
        self.npt = self.pltw.blklst[self.blkno][self.xpos].size
        self.data = np.vstack( (self.pltw.blklst[self.blkno][self.xpos],
                                self.pltw.blklst[self.blkno][self.ypos],
                                np.zeros(self.npt)) )
        self.baslin = []        # (x,y,idx) tuple list of baseline points
        self.BLtyp = 'S'        # 'L' = Linear, 'S' = cubic Spine
        self.BL = None          # Baseline curve not yet plotted
        self.Xpt = None
        self.Ypt = None

        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.canvas.setFocus()
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        self.axes = self.fig.add_subplot(111)

        # Baseline type
        self.BLtyplab = QtWidgets.QLabel("Baseline type")
        self.BLtypComboBox = QtWidgets.QComboBox(self)
        self.typelist = [ "Cubic Spline", "Linear" ]
        self.BLtypComboBox.addItems(self.typelist)

        # Buttons
        addBLBtn = QtWidgets.QPushButton("Add BL")
        subtractBtn = QtWidgets.QPushButton("Correct")
        cancelBtn = QtWidgets.QPushButton("Cancel")

        # set the layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.BLtyplab)
        hbox.addWidget(self.BLtypComboBox)
        hbox.addWidget(addBLBtn)
        hbox.addWidget(subtractBtn)
        hbox.addWidget(cancelBtn)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

        self.BLtypComboBox.currentIndexChanged.connect(self.changeBLTyp)
        self.canvas.mpl_connect('button_press_event', self.onClick)
        addBLBtn.clicked.connect(self.addBL)
        subtractBtn.clicked.connect(self.subtract)
        cancelBtn.clicked.connect(self.reject)
        self.setWindowTitle('Baseline correction tool')
        self.axes.plot(self.data[0], self.data[1], linestyle='-', color='blue')
        self.canvas.draw()


    def changeBLTyp(self):
        """ Callback function when the user change the baseline type.

        :return: nothing
        """
        typ = self.BLtypComboBox.currentIndex()
        if typ == 0:
            self.BLtyp = 'S'
        if typ == 1:
            self.BLtyp = 'L'


    def onClick(self, event):
        """ Callback function when the user clicks with mouse on the plot.

            If left click add a new point in the list at the mouse position
            If right click delete the point which was already around. At least
            two points must be kept.
        :param event: mouse event
        :return: nothing
        """
        if event.inaxes:
            if event.button == 3:
                if len(self.baslin) < 2:
                    # Cannot delete if there less than 2 points
                    return
            elif event.button != 1:
                return
        else:
            return

        xmous, ymous = event.xdata, event.ydata
        tpidx = np.where(self.data[0] >= xmous)
        idx = tpidx[0][0]
        if len(self.baslin) == 0:
            # first point of the baseline
            # disable BL type choice
            self.BLtypComboBox.setEnabled(False)
            ym = self.calcVmoy(self.data[1], idx, 3)
            self.baslin.append((self.data[0][idx], ym, idx))
            # add baseline plot items
            self.data[2] = self.baslin[0][1]
            self.Xpt = list(t[0] for t in self.baslin)
            self.Ypt = list(t[1] for t in self.baslin)
            if self.BLtyp == 'L':
                # plot baseline points linked by segments
                self.BLplt, = self.axes.plot(self.Xpt, self.Ypt, marker='*',
                                             markersize=10, color='red')
            else:
                # plot only baseline points
                self.BLplt, = self.axes.plot(self.Xpt, self.Ypt, marker='*', color='red', linestyle = 'None')
            self.canvas.draw()
        else:
            nbas = len(self.baslin)
            xresol = getSpan(self.data[0])/100
            yresol = getSpan(self.data[1])/100
            if event.button == 3:
                for i in range(nbas):
                    if event.button == 3:
                        # if there is already a point close enough, delete it
                        if abs(xmous - self.baslin[i][0]) < xresol:
                            if abs(ymous - self.baslin[i][1]) < yresol:
                                del self.baslin[i]
                                break
            else:
                # Add the point in the table
                self.baslin.append((self.data[0][idx], self.data[1][idx], idx))
                # The following code was dropped because it was sometimes an issue.
                # In case of noise, smoothing first the date avoid the averaging
                # process below.
                # To reduce the noise effect the y position is recalculated
                # by averaging with 'calcVmoy' function.
                #ym = self.calcVmoy(self.data[1], idx, 3)
                #self.baslin.append((self.data[0][idx], ym, idx))
                # sort the points in x ascending order
                self.baslin = sorted(self.baslin, key=itemgetter(0))
            self.baslinCalc()
            self.updatePlot()


    def calcVmoy(self, V, idx, n):
        """ Return the average value of the vector around the index 'idx'.

            The value is calculated by averaging the point at index 'idx' with
            the n neighbors on each side.

        :param V: Vector V
        :param idx: index of the central point where the average is done.
        :param n: number of neighbors
        :return: Averaged value.
        """
        i = max(idx-n, 0)
        f = min(idx+n+1, V.shape[0])
        av = np.mean(V[i:f])
        return av


    def baslinCalc(self):
        """ Compute the curve defined by linking the points of the baseline.

        :return: nothing
        """
        nbas = len(self.baslin)
        if self.data is None or nbas < 2:
            return

        if self.BLtyp == 'L' and nbas > 1:
            for i in range(nbas-1):
                ideb = self.baslin[i][2]
                ifin = self.baslin[i+1][2]
                slope = (self.data[1][ifin] - self.data[1][ideb]) / (self.data[0][ifin] - self.data[0][ideb])
                intercept = self.data[1][ideb] - slope * self.data[0][ideb]
                if i == 0:
                    l = 0
                else:
                    l = ideb+1
                if i == nbas - 2:
                    ifin = self.npt - 1
                for j in range(l, ifin+1):
                    self.data[2][j] = slope * self.data[0][j] + intercept
        else:
            # spline baseline
            if nbas > 3:
                xbl = list(t[0] for t in self.baslin)
                ybl = list(t[1] for t in self.baslin)
                tck = interpolate.splrep(xbl, ybl, s=0)
                self.data[2] = interpolate.splev(self.data[0], tck, der=0)
        return


    def updatePlot(self):
        """ Udate the plotting area.

        :return: nothing.
        """
        if len(self.baslin):
            X = list(t[0] for t in self.baslin)
            Y = list(t[1] for t in self.baslin)
            self.BLplt.set_xdata(X)
            self.BLplt.set_ydata(Y)
            if self.BLtyp == 'S':
                if self.BL is None:
                    self.BL, = self.axes.plot(self.data[0], self.data[2], linestyle='-', color='green')
                else:
                    self.BL.set_ydata(self.data[2])
        self.canvas.draw()


    def addBL(self):
        """ Callback function when user has clicked on the "add BL" button.

            The baseline vector is added to the data block.

         :return: nothing
         """
        self.parent.copyCurrentWinState(self.pltw)
        vname = self.pltw.curvelist[self.cpos].name + 'BL'
        (nvec, npt) = np.shape(self.pltw.blklst[self.blkno])
        if self.pltw.pasteVector(self.data[2], self.blkno, vname):
            xname = self.pltw.getVnam(self.blkno, self.xpos)
            xvinfo = vectInfo(self.blkno, self.xpos, xname)
            yvinfo = vectInfo(self.blkno, nvec, vname)
            self.pltw.curvelist.append(curveInfo(vname, xvinfo, yvinfo))
        self.pltw.updatePlot()
        self.pltw.dirty = True
        self.pltw.activecurv = self.cpos
        self.parent.updateUI()
        self.hide()


    def subtract(self):
        """ Callback function when user has clicked on OK button.

            The baseline vector is subtracted from the original data vector.

         :return: nothing
         """
        self.parent.copyCurrentWinState(self.pltw)
        self.pltw.blklst[self.blkno][self.ypos] = self.data[1] - self.data[2]
        self.pltw.updatePlot()
        self.pltw.dirty = True
        self.pltw.activecurv = self.cpos
        self.parent.updateUI()
        self.hide()



# noiseDlg --------------------------------------------------------------

class noiseDlg(QtWidgets.QDialog):
    def __init__(self, parent=None, pltw=None, cpos=None):
        """ Interactive Add Noise Tool dialog.

         :param parent: pyDataVis MainWindow.
         :param cpos: it is the curve position in plotWin.curvelist.
         """
        super (noiseDlg, self).__init__(parent)

        self.parent = parent
        self.pltw = pltw
        self.cpos = cpos
        self.blkno = pltw.curvelist[cpos].yvinfo.blkpos
        self.xpos = pltw.curvelist[cpos].xvinfo.vidx
        self.ypos = pltw.curvelist[cpos].yvinfo.vidx
        self.npt = pltw.blklst[self.blkno][self.xpos].size
        self.data = np.vstack( (pltw.blklst[self.blkno][self.xpos],
                                pltw.blklst[self.blkno][self.ypos],
                                pltw.blklst[self.blkno][self.ypos],
                                np.zeros(len(pltw.blklst[self.blkno][self.xpos]))) )
        self.dataSpan = getSpan(self.data[1])
        self.loc = 0.0
        self.scale = self.dataSpan * 0.01

        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.canvas.setFocus()
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)

        self.axes = self.fig.add_subplot(111)
        # Location
        loclab = QtWidgets.QLabel("Location")
        self.loctext = QtWidgets.QLineEdit(self)
        regex = QRegExp("[0-9]+.?[0-9]{,5}")
        validator = QtGui.QRegExpValidator(regex, self.loctext)
        self.loctext.setValidator(validator)
        # Scale
        scalelab = QtWidgets.QLabel("Scale")
        self.scaletext = QtWidgets.QLineEdit(self)
        validator = QtGui.QRegExpValidator(regex, self.scaletext)
        self.scaletext.setValidator(validator)
        # Buttons
        exeBtn = QtWidgets.QPushButton("Compute")
        okBtn = QtWidgets.QPushButton("OK")
        cancelBtn = QtWidgets.QPushButton("Cancel")

        # set the layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(loclab)
        hbox.addWidget(self.loctext)
        hbox.addWidget(scalelab)
        hbox.addWidget(self.scaletext)
        hbox.addWidget(exeBtn)
        hbox.addWidget(okBtn)
        hbox.addWidget(cancelBtn)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

        # Connect buttons to callback functions
        exeBtn.clicked.connect(self.compute)
        okBtn.clicked.connect(self.validate)
        cancelBtn.clicked.connect(self.reject)
        self.setWindowTitle('Add Noise Tool')

        self.initWidgets()
        self.compute()


    def initWidgets(self):
        """ Update the widgets with self.loc and self.scale values.

        :return: nothing
        """
        self.loctext.setText("{0:g}".format(self.loc))
        self.scaletext.setText("{0:g}".format(self.scale))


    def updatePlot(self):
        """ Udate the plotting area.

        :return: nothing.
        """
        self.axes.clear()
        self.axes.plot(self.data[0], self.data[1], linestyle='-', color='gray')
        self.axes.plot(self.data[0], self.data[2], linestyle='-', color='blue')
        self.axes.plot(self.data[0], self.data[3], linestyle='-', color='darkgreen')
        self.canvas.draw()


    def validate(self):
        """ Callback function when user has clicked on OK button.

            The original data is replaced by the vector with interpolated data,

        :return: nothing
        """
        self.pltw.blklst[self.blkno][self.ypos] = self.data[2]
        self.pltw.updatePlot()
        self.pltw.dirty = True
        self.pltw.activecurv = self.cpos
        self.parent.updateUI()
        self.hide()


    def compute(self):
        """ Launch the noise addition process.

        :return: nothing
        """
        # get the parameter values from the widgets
        loc = float(str(self.loctext.text()))
        scale = float(str(self.scaletext.text()))
        # check the values
        # compute
        self.data[2] = self.data[1] + np.random.normal(loc, scale, self.npt)
        self.data[3] = self.data[2] - self.data[1] - self.dataSpan * 0.1
        # store the values
        self.loc = loc
        self.scale = scale
        self.updatePlot()



# deNoiseDlg --------------------------------------------------------------

class deNoiseDlg(QtWidgets.QDialog):
    def __init__(self, parent=None, pltw=None, cpos=None):
        """ Remove Noise Tool dialog.

         :param parent: pyDataVis MainWindow.
         :param cpos: it is the curve position in plotWin.curvelist.
         """
        super (deNoiseDlg, self).__init__(parent)

        self.parent = parent
        self.pltw = pltw
        self.cpos = cpos
        self.blkno = pltw.curvelist[cpos].yvinfo.blkpos
        self.xpos = pltw.curvelist[cpos].xvinfo.vidx
        self.ypos = pltw.curvelist[cpos].yvinfo.vidx
        self.npt = pltw.blklst[self.blkno][self.xpos].size
        self.data = np.vstack( (pltw.blklst[self.blkno][self.xpos],
                                pltw.blklst[self.blkno][self.ypos],
                                pltw.blklst[self.blkno][self.ypos],
                                np.zeros(len(self.pltw.blklst[self.blkno][self.xpos]))) )

        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.canvas.setFocus()
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)

        self.axes = self.fig.add_subplot(111)
        # Buttons
        okBtn = QtWidgets.QPushButton("OK")
        cancelBtn = QtWidgets.QPushButton("Cancel")

        # set the layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(okBtn)
        hbox.addWidget(cancelBtn)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

        # Connect buttons to callback functions
        okBtn.clicked.connect(self.validate)
        cancelBtn.clicked.connect(self.reject)
        self.setWindowTitle('Remove Noise Tool')

        self.dataSpan = getSpan(self.data[1])
        self.compute()


    def updatePlot(self):
        """ Udate the plotting area.

        :return: nothing.
        """
        self.axes.clear()
        self.axes.plot(self.data[0], self.data[1], linestyle='-', color='blue')
        self.axes.plot(self.data[0], self.data[2], linestyle='-', color='red')
        self.axes.plot(self.data[0], self.data[3], linestyle='-', color='gray')
        self.canvas.draw()


    def validate(self):
        """ Callback function when user has clicked on OK button.

            The original data is replaced by the vector with noisy data,

        :return: nothing
        """
        self.pltw.blklst[self.blkno][self.ypos] = self.data[2]
        self.pltw.updatePlot()
        self.pltw.dirty = True
        self.pltw.activecurv = self.cpos
        self.parent.updateUI()
        self.hide()


    def compute(self):
        """ Launch the noise removal process.

        :return: nothing
        """
        Y = self.data[1]
        # Create an order 3 lowpass butterworth filter
        b, a = signal.butter(3, 0.05)
        # Apply the filter to Y. Use lfilter_zi to choose the initial condition of the filter
        zi = signal.lfilter_zi(b, a)
        z, _ = signal.lfilter(b, a, Y, zi=zi * Y[0])
        # Apply the filter again, to have a result filtered at an order the same as filtfilt
        z2, _ = signal.lfilter(b, a, z, zi=zi * z[0])
        # Use filtfilt to apply the filter
        self.data[2] = signal.filtfilt(b, a, Y)
        self.data[3] = self.data[2] - self.data[1] - self.dataSpan * 0.3
        self.updatePlot()


