""" This module contains the script class

    A script is a command.
    There is 4 types of commands:
        
    type 0 = no argument
        BET, BETKr, BETAr, PSD, IRabs, IRtrans

    type 1 = commands with one argument (generally the vector name)
        del X, stats Y, area V1, line V1, lineq V1, revert Y,
        sort Y, delMulX Y, onset Y, fft Y, symbol Y, nosymbol Y

    type 2 = commands with two arguments
        clipup Y1 10
        clipdn Y2 0
        clipx < 10
        clipx > 100
        shift V1 -0.5
        shrink V1 5
        linefit V1 -1
        despike V1 winsiz
        ndec Y 5

    type 3 = commands for operation on vectors or between vectors
        Y2 = Y1
        Y1 = Y1 * 5.0
        Y1 = Y1 / 10
        Y1 = Y1 - Y2
        Y2 = log(Y1)
        Y3 = grad(Y1)
        Y3 = sum(Y1)

    type 4 = rename command
        name Y1 as Y2

    type 5 = new command
        new X 0,10,1
"""

import os
import numpy as np
from scipy import signal

from utils import (isNumber, calcArea, shrinkRows, sortArr,
                                 delDupliX, rms, pp)
from convert import convertToAbs, convertToTrans
from convIso import BET, PSDcalc
from plotWindow import vectInfo, lineSeg


class script(object):
    """ A script is a command.

        Empty lines and lines starting with # are ignored for execution
        script must be called by a plotWin.
    """

    def __init__(self, parent):
        self.parent = parent
        self.operators = set( '+-*/()' )
        self.npfunc = ['arccos', 'arccosh', 'arcsin', 'arcsinh', 'arctan',
                       'arctanh', 'cos', 'cosh', 'cumsum', 'cumprod', 'exp',
                       'fabs', 'gradient', 'log', 'log10', 'power',
                       'sin', 'sinh', 'sqrt', 'square', 'tan', 'tanh']
        self.typ0Lst = [ 'BET', 'BETKr', 'BETAr', 'IRabs', 'IRtrans',
                         'invertx', 'inverty']
        self.typ1Lst = [ 'delv', 'delb', 'stats', 'area', 'line', 'lineq',
                         'revertb', 'revertv', 'sort', 'deldupx', 'onset',
                         'fft' ]
        self.typ2Lst = [ 'swapv', 'mergeb', 'clipup', 'clipdn', 'clipx',
                         'linefit', 'shift', 'shrink', 'despike', 'ndec',
                         'PSD' ]
        self.typ4Lst = [ 'name' ]
        self.typ5Lst = [ 'newv' ]



    def checkType(self, cmd):
        """ Check the type of the command 'cmd'

        :param cmd: a string containing the command
        :return: a tuple containing the command type and the number of
                 arguments. Return (None,0) if the command was not found.
        """
        cmd = cmd.strip()
        if len(cmd) == 0 or cmd[0] == '#':
            # Empty command
            return (None, 0)

        items = cmd.split(' ')
        nitems = len(items)
        narg = nitems - 1
        # Is it a new command (type = 5)
        if cmd.startswith('newv'):
            return (5, narg)
        # Is it a rename command (type = 4) ?
        if cmd.startswith('name'):
            return (4, narg)
        # Is it an expression or operation command (type = 3) ?
        if cmd.find('=') != -1:
            return (3, narg)
        if nitems == 3:
            # It is a two arg command (type = 2)
            return (2, narg)
        if nitems == 2:
            # It is a one arg command (type = 1)
            return (1, narg)
        if nitems == 1:
           # It is a command without argument
           return (0, narg)
        return (None, -1)


    def lookForCmd(self, cmd):
        """ Check if 'cmd' contains a valid command.

        :param cmd: a string containing the command
        :return: a tuple containing the command type and the expected number
                 number of arguments. Return (None,0) if the command was not
                 found.
        """
        cmd = cmd.strip()
        items = cmd.split(' ')
        if len(items) == 1:
            cmdnam = cmd
        else:
            cmdnam = items[0]
        if cmdnam in self.typ0Lst:
            return (0,0)
        if cmdnam in self.typ1Lst:
            return (1,1)
        if cmdnam in self.typ2Lst:
            return (2,2)
        if cmdnam in self.typ4Lst:
            return (4,3)
        if cmdnam in self.typ5Lst:
            return (5,2)
        return (None,0)



    def dispatch(self, cmd):
        """ Check the type of the command 'cmd'

            Call the corresponding exe function.
        :param cmd: a string containing the command
        :return: a tuple (err, msg).
            The behavior of the calling function when returning is expected to be:
            if err = 0 and mgs = "" update the plot
            if err = 0 and msg != "" shows the message in information window
            if err > 0 and msg != "" shows the message in QMessageBox.warning
            if err < 0 and msg != "" shows the message in information window and update the plot
        """
        if cmd.find('=') != -1:
            # this is an expression
            typ = 3
            narg = -1
        else:
            # If this is not an expression check the command name
            # Remove space after comma
            cmd = cmd.replace(", ", ",")
            typ, narg = self.lookForCmd(cmd)
            if typ is None:
                return (1, "Unknown command")

        typ2, narg2 = self.checkType(cmd)
        if typ2 is None:
            if narg2 == 0:
                return (1, "Empty command")
            else:
                return (1, "Unable to process command")
        if typ == 3:  # expression or operation command
            return self.exeExpression(cmd)

        if narg2 < narg:
            return (1, "Not enough parameters")
        if narg2 > narg:
            return (1, "Too much parameters")
        if typ == 5:  # new command
            return newV(self.parent, cmd)
        elif typ == 4:  # rename command
            return name(self.parent, cmd)
        elif typ == 2:  # command with two argument
            return self.exeTwoArg(cmd)
        elif typ == 0:  # command with no argument
            return self.exeNoArg(cmd)
        else:
            # It is a one arg command
            items = cmd.split(' ')
            # look for the command name
            try:
                cmdidx = self.typ1Lst.index(items[0])
            except ValueError:
                    return (1, "Check the parameters")
            # look for the vector name
            if self.parent.getVinfo(items[1]) is None:
                # vector not found, is it a number ?
                if isNumber(items[1]):
                    if items[0] == "delb":
                        blkno = items[1]
                        nblk =  len(self.parent.blklst)
                        if int(blkno) < 0 and int(blkno) > nblk:
                            return (1, "Wrong block number")
                else:
                    if items[0] == "delb":
                        return (1, "Wrong block number")
                    else:
                        return (1, "Unknown vector name")
            return self.exeOneArg(cmdidx, items[1])


    def exeExpression(self, cmd):
        """ Process the commands containing an expression.

            Expression means that the command contains '='.
        :param cmd: a string containing the command
        :return: a tuple (errno, errmsg).
        """
        items = cmd.split('=')
        vnam = items[0].strip()
        expression = items[1].strip()

        # Build vector name list
        # Build vector ndarray list
        vectLst = []
        vectNam = []
        for i in range(len(self.parent.vectInfolst)):
            for j in range(len(self.parent.vectInfolst[i])):
                vectNam.append(self.parent.vectInfolst[i][j].name)
                vectLst.append(self.parent.blklst[i][j])

        # Check that all the vectors in expression belong to the same data block
        first = True
        for vn in vectNam:
            if vn in expression:
                vinfo = self.parent.getVinfo(vn)
                blkno = vinfo.blkpos
                if first:
                    first = False
                else:
                    if vinfo.blkpos != blkno:
                        return (1, "All vectors must belong "
                                   "to the same datablock")
                    break

        # Check expression for unauthorized functions or unknown vector name
        # The goal is to secure the use of eval. Besides check that all
        # the vectors belong to the same data block.
        blkno = -1
        s = expression
        for c in self.operators:
            s = s.replace(c, ',')
        items = s.split(',')
        for item in items:
            item = item.strip()
            if item:
                if not item in vectNam:
                    if not item in self.npfunc:
                        if not isNumber(item):
                            return (1, "Unknown vector or function")
                else:
                    if blkno == -1:
                        blkno = self.parent.getVinfo(item).blkpos
                    else:
                        if self.parent.getVinfo(item).blkpos != blkno:
                            return (1, "All vectors must belong to the same data block")

        # Prefix, in expression, the function name with 'np.'
        for fn in self.npfunc:
            if fn in expression:
                expression = expression.replace(fn, "np.{0}".format(fn))

        # Build the nam: ndarray dictionary for eval
        dictVec = {vectNam[i]: vectLst[i] for i in range(len(vectNam))}

        try:
            R = eval(expression, globals(), dictVec)
        except SyntaxError:
            # If the user enters an invalid expression
            return (1, "Invalid command syntax")
        except (NameError, ValueError) as err:
            # If the user tries to use a name that isn't allowed
            # or an invalid value for a given math function
            return (1, err)

        vinfo = self.parent.getVinfo(vnam)
        if vinfo is not None:
            nelem = self.parent.blklst[vinfo.blkpos][vinfo.vidx].size
            try:
                rsiz = R.size
            except AttributeError:
                # R is not a vector
                if isNumber(R):
                    self.parent.blklst[vinfo.blkpos][vinfo.vidx] = np.full(nelem, R)
                else:
                    return (1, "Invalid command syntax")
            if rsiz == nelem:
                self.parent.blklst[vinfo.blkpos][vinfo.vidx] = R
            else:
                return (1, "Vector size do not match")
        else:
            # If the vector does not exist, check if it is in expression
            if expression.find(vnam) != -1 or expression.find("("+vnam+")") != -1:
                return (1, "Unknown vector name")
            # Add a new vector at the end of a data block
            if blkno == -1:
                if not hasattr(R, "__len__"):
                    # R is not a vector
                    return (1, "Cannot process this command")
                # Look for a data block size matching R.size
                for i in range(len(self.parent.blklst)):
                    if self.parent.blklst[i][0].size == R.size:
                        blkno = i
                        break
            if blkno == -1:
                # No block size match R.size
                return (1, "Vector size do not match")
            s = np.shape(self.parent.blklst[blkno])
            nlin = s[0]
            if len(s) > 1:
                nrow = s[1]
            else:
                nrow = nlin
                nlin = 1
            vinfo = vectInfo(blkno, nlin, vnam)
            # add the new vector
            self.parent.vectInfolst[blkno].append(vinfo)
            newvect = R
            newset = np.vstack((self.parent.blklst[blkno], newvect))  # vstack = data stacked in row
            self.parent.blklst[blkno] = newset
        self.parent.dirty = True
        return (0, "")


    def exeNoArg(self, cmd):
        """ Process the commands with no argument

        :param cmd: a string containing the command
        :return: a tuple (errno, errmsg).
        """
        # look for the command name
        errno = 0
        msg = ""
        try:
            cmdidx = self.typ0Lst.index(cmd)
        except ValueError:
            return (1, "Check the parameters")
        logfilnam = os.path.join(self.parent.parent.progpath, "logfile.txt")
        if cmdidx == self.typ0Lst.index('BET'):
            errno, msg = BET(self.parent.blklst[0], 'N2', logfilnam)
        elif cmdidx == self.typ0Lst.index('BETKr'):
            errno, msg = BET(self.parent.blklst[0], 'Kr', logfilnam)
        elif cmdidx == self.typ0Lst.index('BETAr'):
            errno, msg = BET(self.parent.blklst, 'Ar', logfilnam)
        elif cmdidx == self.typ0Lst.index('IRabs'):
            errno, msg = convertToAbs(self.parent.blklst[0])
            if not errno:
                self.parent.laby1 = "Absorbance"
                self.parent.vectInfolst[0][1].name = 'Absorbance'
        elif cmdidx == self.typ0Lst.index('IRtrans'):
            errno, msg = convertToTrans(self.parent.blklst[0])
            if not errno:
                self.parent.laby1 = "Transmittance"
                self.parent.vectInfolst[0][1].name = 'Transmittance'
        elif cmdidx == self.typ0Lst.index('invertx'):
            self.parent.invertX = not(self.parent.invertX)
            return errno, msg
        elif cmdidx == self.typ0Lst.index('inverty'):
            self.parent.invertY = not(self.parent.invertY)
            return errno, msg
        else:
            return (1, "Internal error")
        if errno == 0:
            if cmdidx > 3:       # cmdidx <= 3 for BET and PSD
                self.parent.dirty = True
        return (errno, msg)


    def exeOneArg(self, cmdidx, vnam):
        """ Process the commands with one argument

        :param cmdidx: index of the command in self.typ1Lst
        :param vnam: name of the vector argument.
        :return: a tuple (err, msg).
                 err = 0 means no error
                 err = 1 means an error occurred
                 err =-1 means no error
        """
        if not isNumber(vnam):
            vinfo = self.parent.getVinfo(vnam)
            blkno = vinfo.blkpos
            vpos = vinfo.vidx
        else:
            blkno = None
            vpos = None

        if cmdidx == self.typ1Lst.index('stats'):
            err, result = stats(self.parent, vnam)
            return (0, result)

        if cmdidx == self.typ1Lst.index('area'):
            # check that the range is defined
            if len(self.parent.markList) == 1:
                return (1, "Range must be defined (with markers)")
            else:
                curvinfo = self.parent.getCurvinfo(vnam)
                if curvinfo is None:
                    return (1, "Unknown curve")
                if len(self.parent.markList) == 0:
                    idx1 = None
                    idx2 = None
                else:
                    idx1 = self.parent.markList[0].getIndex()
                    idx2 = self.parent.markList[1].getIndex()
                result = calculArea(self.parent, curvinfo, idx1, idx2)
                return (0, result)

        if cmdidx == self.typ1Lst.index('lineq'):
            if len(self.parent.markList) != 2:
                return (1, "Range must be defined (with markers)")
            else:
                curvinfo = self.parent.getCurvinfo(vnam)
                if curvinfo is None:
                    return (1, "Wrong curve name")
                idx1 = self.parent.markList[0].getIndex()
                idx2 = self.parent.markList[1].getIndex()
                err, msg = linEq(self.parent, curvinfo, idx1, idx2)
                if not err:
                    x1 = self.parent.blklst[0][0][20]
                    y1 = self.parent.blklst[0][1][20]
                    x2 = self.parent.blklst[0][0][60]
                    y2 = self.parent.blklst[0][1][60]
                    self.parent.lineList.append(lineSeg(x1, y1, x2, y2, 'red'))
                    self.parent.updatePlot()
                return err, msg

        if cmdidx == self.typ1Lst.index('delb'):
            blkno = int(vnam) - 1
            if self.parent.delBlock(blkno):
                return (0, "")
            else:
                return (1, "Cannot delete this data block")

        if cmdidx == self.typ1Lst.index('delv'):
            if self.parent.delVector(vnam):
                return (0, "")
            else:
                return (1, "Cannot delete this vector")

        if cmdidx == self.typ1Lst.index('line'):
            # Join by a straight line the mark positions
            err, errmsg = line(self.parent, vnam)
            if not err:
                self.parent.dirty = True
                self.parent.clearMarks()
            return (err, errmsg)

        if cmdidx == self.typ1Lst.index('revertb'):
            # Revert data order in data block
            blkno = int(vnam) - 1
            err, errmsg = revertb(self.parent, blkno)
            if not err:
                self.parent.dirty = True
                self.parent.clearMarks()
                errmsg = "The data order in all the vectors in block {0}" \
                         " has been reverted".format(blkno+1)
                err = -1
            return (err, errmsg)

        if cmdidx == self.typ1Lst.index('revertv'):
            # Revert data order in vnam
            err, errmsg = revertv(self.parent, vnam)
            if not err:
                self.parent.dirty = True
                self.parent.clearMarks()
            return (err, errmsg)

        if cmdidx == self.typ1Lst.index('sort'):
            # Sort vnam in ascending order.
            err, errmsg = sort(self.parent, vnam)
            if not err:
                self.parent.dirty = True
                self.parent.clearMarks()
                errmsg = "The vector {0} has been sorted" \
                         " in ascending order".format(vnam)
                err = -1
            return (err, errmsg)

        if cmdidx == self.typ1Lst.index('deldupx'):
            # Sort X in ascending order and remove duplicate values.
            err, errmsg = delDupX(self.parent, vnam)
            if not err:
                err = -1
                self.parent.dirty = True
                self.parent.clearMarks()
            return (err, errmsg)

        if cmdidx == self.typ1Lst.index('onset'):
            if len(self.parent.markList) != 2:
                return (1, "Positions must be defined (with markers)")
            else:
                curvinfo = self.parent.getCurvinfo(vnam)
                idx1 = self.parent.markList[0].getIndex()
                idx2 = self.parent.markList[1].getIndex()
                err, msg = onset(self.parent, curvinfo, idx1, idx2)
                return (err, msg)

        if cmdidx == self.typ1Lst.index('fft'):
            err, errmsg = fft(self.parent, vnam)
            return (err, errmsg)

        else:          # unknown command
            return (1, "Check the parameters")



    def exeTwoArg(self, cmd):
        """  Process the commands with two arguments.

             The commands clipup and clipdn are processed here
             although they have 3 arguments.

        :param cmd: a string containing the command name.
        :return: a tuple (errno, errmsg).
        """
        items = cmd.split(' ')
        cmdname = items[0].strip()
        # look for the command name
        try:
            cmdidx = self.typ2Lst.index(cmdname)
        except ValueError:
            return (1, "Check the parameters")

        if cmdname == 'mergeb':
            # Syntax is mergeb blk1 blk2
            err, msg = mergeb(self.parent, items[1:])
            if not err:
                self.parent.dirty = True
            return err, msg

        if cmdname == 'PSD':
            # Syntax is: PSD D halsey
            # use adsorption isotherm
            pos = 0
            if items[1].strip() == 'D':
                if len(self.parent.blklst) > 1:
                    # use desorption isotherm stored in the second data block.
                    pos = 1
                else:
                    # no adsorption isotherm only
                    # one desorption isotherm
                    pos = 0
            dirnam = os.path.dirname(self.parent.filename)
            basenam = os.path.basename(self.parent.filename)
            psdnam = basenam.replace("iso", "PSD")
            if psdnam == basenam:
                psdnam = "PSD.txt"
            psdnam = os.path.join(dirnam, psdnam)
            tcurv = items[2].strip()
            if tcurv in ['halsey', 'harkins', 'tfit']:
                errno, msg = PSDcalc(self.parent.blklst[pos], psdnam, tcurv)
            else:
                errno, msg = PSDcalc(self.parent.blklst[pos], psdnam)
            if not errno:
                msg = self.parent.parent.loadFile(psdnam)
            return 0, msg

        # The vector name is expected to be the 2nd argument (items[1))
        # except for the clipx command
        vnam = items[1].strip()
        if vnam != '<' and vnam != '>':
            # it not a clipx command
            vinfo = self.parent.getVinfo(vnam)
            if vinfo is None:
                return (1, "Unknown vector name")
            blkno = vinfo.blkpos
            vidx = vinfo.vidx

        # check value
        if isNumber(items[2]):
            val = float(items[2])
        else:
            v2nam = items[2].strip()

        if cmdname == 'swapv':
            # the syntax is: swapv V1 V2
            err, msg = swapv(self.parent, vnam, v2nam)
            if not err:
                self.parent.dirty = True
            return err, msg

        elif cmdname =='clipup':
            # the syntax is: clipup V > n
            err, msg = clipup(self.parent, vnam, val)
            if err and msg == "":
                err = 0
            else:
                self.parent.dirty = True
            return err, msg

        elif cmdname =='clipdn':
            # The syntax is: clipdn V > n
            err, msg = clipdn(self.parent, vnam, val)
            if err and msg == "":
                err = 0
            else:
                self.parent.dirty = True
            return err, msg

        elif cmdname =='clipx':
            # The syntax is: clipx < n
            err, msg = clipx(self.parent, val, vnam)
            if not err:
                self.parent.dirty = True
            return err, msg

        elif cmdname == 'linefit':
            # The syntax is: linefit V -1
            # check that the cursor position is defined
            if self.parent.dcursor is None:
                return (1, "Position must be defined (with cursor)")
            else:
                curvinfo = self.parent.getCurvinfo(vnam)
                idx = self.parent.dcursor.getIndex()
                err, result = lineFit(self.parent, curvinfo, idx, val)
                return err, result

        elif cmdname == 'shift':
            # The syntax is: shift V n
            if len(self.parent.markList) != 2:
                return (1, "Range must be defined (with markers)")
            else:
                curvinfo = self.parent.getCurvinfo(vnam)
                if curvinfo is None:
                    return (1, "Wrong curve name")
                idx1 = self.parent.markList[0].getIndex()
                idx2 = self.parent.markList[1].getIndex()
                err, msg = shift(self.parent, curvinfo, val, idx1, idx2)
                if not err:
                    self.parent.dirty = True
                return err, msg

        elif cmdname == 'shrink':
            # The syntax is: shrink V n
            factor = int(val)
            err, msg = shrink(self.parent, vnam, factor)
            if not err:
                self.parent.dirty = True
            return err, msg

        elif cmdname == 'despike':
            # The syntax is despike V winsiz
            winsiz = int(val)
            err, msg = despike(self.parent, vnam, winsiz)
            if not err:
                self.parent.dirty = True
            return err, msg

        elif cmdname == 'ndec':
            # Syntax is: ndec V n
            nd = int(items[2])
            err, msg = ndec(self.parent, vnam, nd)
            if not err:
                msg = "The number of decimal place of vector {0} was set to {1}".format(vnam, ndec)
                self.parent.dirty = True
            return err, msg

        else:
            return(1, "Unable to process command")



def name(pltw, cmd):
    """ Process a rename command

        :param pltw: plotWin containing data
        :param cmd: a string containing the command
        :return: a tuple (errno, errmsg).
    """
    # The syntax is: 'name oldnam as newnam'
    if cmd.find('as') == -1:
        return 1, "Check the parameters"
    cmd = cmd[5:]
    items = cmd.split('as')
    oldnam = items[0].strip()
    newnam = items[1].strip()
    vinfo = pltw.getVinfo(newnam)
    if vinfo is not None:
        return 1, "This name already exists"
    vinfo = pltw.getVinfo(oldnam)
    if vinfo is None:
        return 1, "Unknown vector name"
    vinfo.name = newnam
    # update pltw.curvelist
    for curvinfo in pltw.curvelist:
        if curvinfo.name == oldnam:
            curvinfo.name = newnam
    pltw.dirty = True
    return 0, ""


def newV(pltw, cmd):
    """ Process a new vector command

        :param pltw: plotWin containing data
        :param cmd: a string containing the command
        :return: a tuple (errno, errmsg).
    """
    errmsg = ""
    # The syntax is : newv V start,stop,step
    # Remove the cmommand name
    cmd = cmd[5:]

    items = cmd.split(' ')
    vname = items[0]
    n = len(vname)
    cmd = cmd[n:]
    items = cmd.split(',')
    # Check the user input
    if len(items) != 3:
        errmsg = "The syntax of this command is :\n" \
                 " Name Vini, Vend, step"
        return 1, errmsg

    # Check if a vector with the same name already exists
    if pltw.vectInfolst:
        vinfo = pltw.getVinfo(vname)
        if vinfo is not None:
            errmsg = "A vector {0} already exists".format(vname)
            return 1, errmsg

    # Check if Vini, Vend, step are numbers
    if isNumber(items[0]):
        start = float(items[0])
    else:
        errmsg = "Starting value must be a number"
        return 1, errmsg
    if isNumber(items[1]):
        stop = float(items[1])
    else:
        errmsg = "Ending value must be a number"
        return 1, errmsg
    if isNumber(items[2]):
        step = float(items[2])
    else:
        errmsg = "Step value must be a number"
        return 1, errmsg

    # Create the data list
    stop = stop + step
    newv = np.arange(start, stop, step)
    # Create a new data block for the new vector
    if pltw.blklst is None:
        pltw.blklst = []
    # add the new block at the end of block list
    pltw.blklst.append([newv])
    blkpos = len(pltw.blklst) - 1
    # Create the new vectInfo object
    vinfo = vectInfo(blkpos, 0, vname)
    # Add the new vectInfo to the list of vectInfo list
    vectInfolst = []
    vectInfolst.append(vinfo)
    pltw.vectInfolst.append(vectInfolst)
    pltw.dirty = True
    return 0, errmsg


def stats(pltw, vnam):
    """ Return statistics on vnam'.

        :param pltw: plotWin containing data
        :param vnam: the name of the relevant vector.
        :return: a tuple (err, msg) where err = 1 if an error occurred,
                 and msg contains the error message.
    """
    vinfo = pltw.getVinfo(vnam)
    if vinfo is None:
        return 1, "Unknown vector name"
    blkno = vinfo.blkpos
    vpos = vinfo.vidx
    result = "Statistics on {0}:\n".format(vnam)
    val = pltw.blklst[blkno][vpos].min()
    result += "   Mini = {0:g}\n".format(val)
    val = pltw.blklst[blkno][vpos].max()
    result += "   Maxi = {0:g}\n".format(val)
    val = val - pltw.blklst[blkno][vpos].min()
    val = val / (pltw.blklst[blkno][vpos].size - 1)
    dv = abs(pltw.blklst[blkno][vpos][1] - pltw.blklst[blkno][vpos][0])
    if dv == val:
        s = "constant"
    else:
        s = "average"
    result += "   Delta = {0:g},  {1}\n".format(val, s)
    val = pltw.blklst[blkno][vpos].sum()
    result += "   Sum = {0:g}\n".format(val)
    val = np.median(pltw.blklst[blkno][vpos])
    result += "   Median = {0:g}\n".format(val)
    val = pltw.blklst[blkno][vpos].mean()
    result += "   Mean = {0:g}\n".format(val)
    val = pltw.blklst[blkno][vpos].std()
    result += "   Standard deviation = {0:g}\n".format(val)
    val = pltw.blklst[blkno][vpos].var()
    result += "   Variance = {0:g}\n".format(val)
    val = rms(pltw.blklst[blkno][vpos])
    result += "   Root mean square (RMS) = {0:g}\n\n".format(val)
    val = pp(pltw.blklst[blkno][vpos])
    result += "Peak-to-peak (pp) = {0:g}\n".format(val)
    return 0, result


def swapv(pltw, vnam1, vnam2):
    """ Exchange all elements between vectors named 'vnam1' and 'vnam2'.

        Of course these vectors must have the same size.
        Does not change the names.
        :param pltw: plotWin containing data
        :param vnam: the name of the relevant vector.
        :return: a tuple (err, msg) where err = 1 if an error occurred,
                 and msg contains the error message.
    """
    v1info = pltw.getVinfo(vnam1)
    if v1info is not None:
        v2info = pltw.getVinfo(vnam2)
    if v1info is None or v2info is None:
        return 1, "Unknown vector name"
    blkno1 = v1info.blkpos
    blkno2 = v2info.blkpos
    if blkno1 != blkno2:
        if pltw.blklst[blkno1][v1info.vidx].size != pltw.blklst[blkno2][v2info.vidx].size:
            return 1, "Both vectors must have the same size"
    tmp = pltw.blklst[blkno2][v2info.vidx].copy()
    pltw.blklst[blkno2][v2info.vidx] = pltw.blklst[blkno1][v1info.vidx]
    pltw.blklst[blkno1][v1info.vidx] = tmp
    return 0, ""


def shrink(pltw, vnam, n):
    """ Reduce in the number of elements in 'vnam' by a factor 'n'.

       :param pltw: plotWin containing data
       :param vnam: the name of the relevant vector.
       :return: a tuple (err, msg) where err = 1 if an error occurred,
                and msg contains the error message.
    """
    vinfo = pltw.getVinfo(vnam)
    if vinfo is None:
        return 1, "Unknown vector name"
    blkno = vinfo.blkpos
    if 1 < n < 10:
        ni = pltw.blklst[blkno][0].size
        pltw.blklst[blkno] = shrinkRows(pltw.blklst[blkno], n)
        nf = pltw.blklst[blkno][0].size
        msg = "The number of elements in {0} has been reduced " \
              "from {1} to {2}".format(vnam, ni, nf)
        return 0, msg
    else:
        return 1, "Shrink factor must be in range 2-10"


def despike(pltw, vnam, winsiz):
    """ Removes spikes, which point width are lower than winsiz, in 'vnam'.

       :param pltw: plotWin containing data
       :param vnam: the name of the relevant vector.
       :param winsiz: size, in number of points, of the largest spike to remove.
       :return: a tuple (err, msg) where err = 1 if an error occurred,
                and msg contains the error message.

    """
    vinfo = pltw.getVinfo(vnam)
    if vinfo is None:
        return 1, "Unknown vector name"
    blkno = vinfo.blkpos
    vidx = vinfo.vidx
    npt = pltw.blklst[0][vidx].size
    if isNumber(winsiz) and winsiz < 3 and (winsiz > int(npt / 10)):
        return 1, "Bad window size"
    if not winsiz % 2:
        return 1, "winsiz must be an odd integer"
    else:
        pltw.blklst[blkno][vidx] = signal.medfilt(pltw.blklst[blkno][vidx], winsiz)
        return 0, ""


def ndec(pltw, vnam, ndec):
    """ Set the number of decimal places to n for all 'vnam' elements.

        :param pltw: plotWin containing data
        :param vnam: the name of the relevant vector.
        :param ndec: the number of decimal places
        :return: a tuple (err, msg) where err = 1 if an error occurred,
                 and msg contains the error message.
    """
    vinfo = pltw.getVinfo(vnam)
    if vinfo is None:
        return 1, "Unknown vector name"
    blkno = vinfo.blkpos
    vidx = vinfo.vidx
    if isNumber(ndec) and ndec > 0 or ndec > 15:
        v = 10 ** ndec
        pltw.blklst[blkno][vidx] *= v
        pltw.blklst[blkno][vidx] = np.ceil(pltw.blklst[0][vidx])
        pltw.blklst[blkno][vidx] /= v
        return 0, ""
    else:
        return 1, "Invalid number of decimal"


def line(pltw, cnam):
    """ Join by a straight line the marker positions on the curve 'cnam'.

        :param pltw: plotWin containing data
        :param vnam: the name of the relevant curve.
        :return: a tuple (err, msg) where err = True if an error occurred,
                 and msg contains the error message.
    """
    if len(pltw.markList) != 2:
        return 1, "Need two marks to process"
    # check that vnam is a curve
    cinfo = pltw.getCurvinfo(cnam)
    if cinfo is None:
        return 1, "No curve matches with {0}".format(cnam)
    i1 = pltw.markList[0].getIndex()
    i2 = pltw.markList[1].getIndex()
    blkno = cinfo.yvinfo.blkpos
    X = pltw.blklst[blkno][cinfo.xvinfo.vidx]
    Y = pltw.blklst[blkno][cinfo.yvinfo.vidx]
    if X[i2] < X[i1]:
        i = i1
        i1 = i2
        i2 = i
    intercept = Y[i1]
    slope = (Y[i2] - Y[i1]) / (X[i2] - X[i1])
    for i in range(i1, i2):
        Y[i] = slope * (X[i] - X[i1]) + intercept
    return 0, ""


def revertb(pltw, blkno):
    """ Revert data order in the data block 'blkno'

        :param pltw: plotWin containing data
        :param blkno: the position of the data block which will be processed.
        :return: a tuple (err, msg) where err = True if an error occurred,
                 and msg contains the error message.
    """
    if blkno < 0 or blkno >= len(pltw.blklst):
        return 1, "Wrong block data number"
    pltw.blklst[blkno] = np.array([x[::-1] for x in pltw.blklst[blkno]])
    return 0, ""


def revertv(pltw, vnam):
    """ Revert data order in the vector 'vnam'

        :param pltw: plotWin containing data
        :param vnam: the name of the vector which will be processed.
        :return: a tuple (err, msg) where err = True if an error occurred,
                 and msg contains the error message.
    """
    errno = 0
    errmsg = ""
    vinfo = pltw.getVinfo(vnam)
    if vinfo is None:
        return 1, "Cannot find vector {0}".format(vnam)
    blkno = vinfo.blkpos
    vidx = vinfo.vidx
    pltw.blklst[blkno][vidx] = (pltw.blklst[blkno][vidx])[::-1]
    return errno, errmsg



def sort(pltw, vnam):
    """ Sort 'vnam' in ascending order.

        Process only the data block containing the vector 'vnam'.
        :param pltw: plotWin containing data
        :param vnam: name of the vector which will be sorted
        :return: a tuple (err, msg) where err = 1 if an error occurred,
                 and msg contains the error message.
    """
    vinfo = pltw.getVinfo(vnam)
    if vinfo is None:
        return 1, "Cannot find vector {0}".format(vnam)
    blkno = vinfo.blkpos
    vidx = vinfo.vidx
    pltw.blklst[blkno] = sortArr(pltw.blklst[blkno], vidx)
    return 0, ""


def delDupX(pltw, Xnam):
    """ First sort 'Xnam' in ascending order and then remove duplicates.

        Process only the data block containing the vector 'Xnam'.
        :param pltw: plotWin containing data
        'Xnam' must be the first vector of the data block.
        :param Xnam: the name of the X vector.
        :return: a tuple (err, msg) where err = 1 if an error occurred,
                 and msg contains the error message.
    """
    vinfo = pltw.getVinfo(Xnam)
    if vinfo is None:
        return 1, "Cannot find vector {0}".format(Xnam)
    blkno = vinfo.blkpos
    vidx = vinfo.vidx
    if vidx != 0:
        return 1, "{0} must be the first vector of the data block".format(Xnam)
    ni = pltw.blklst[blkno][0].size
    pltw.blklst[blkno] = delDupliX(pltw.blklst[blkno], vidx)
    nf = pltw.blklst[blkno][0].size
    dn = ni - nf
    if dn == 0:
        msg = "No duplicate elements has been found in {0}".format(Xnam)
    else:
        msg = "{0} duplicate elements has been deleted in {1}".format(dn, Xnam)
    return 0, msg


def clipup(pltw, vnam, val):
    """ Replace in the vector named 'vnam' all elements larger than val by val.

        :param pltw: plotWin containing data
        :param vnam: name of the relevant vector
        :param val: limit value
        :return: a tuple error value (=0 if no error) and error message
                 (="" if no error). If 'val' is higher than the maximum,
                 return err=1 and msg="" to indicate that nothing was done.
    """
    vinfo = pltw.getVinfo(vnam)
    if vinfo is None:
        return 1, "Cannot find vector {0}".format(vnam)
    blkno = vinfo.blkpos
    vidx = vinfo.vidx
    vm = np.amax(pltw.blklst[blkno][vidx])
    if vm <= val:
        return 1, ""
    vm = np.amin(pltw.blklst[blkno][vidx])
    pltw.blklst[blkno][vidx] = np.clip(pltw.blklst[blkno][vidx], vm, val)
    return 0, ""


def clipdn(pltw, vnam, val):
    """ Replace in the vector named 'vnam' all elements lower than val by val.

        :param pltw: plotWin containing data
        :param vnam: name of the relevant vector
        :param val: limit value
        :return: a tuple error value (=0 if no error) and error message
                 (="" if no error). If 'val' is lower than the minimum,
                 return err=1 and msg="" to indicate that nothing was done.
    """
    vinfo = pltw.getVinfo(vnam)
    if vinfo is None:
        return 1, "Cannot find vector {0}".format(vnam)
    blkno = vinfo.blkpos
    vidx = vinfo.vidx
    vm = np.amin(pltw.blklst[blkno][vidx])
    if vm >= val:
        return 1, ""
    vm = np.amax(pltw.blklst[blkno][vidx])
    pltw.blklst[blkno][vidx] = np.clip(pltw.blklst[blkno][vidx], val, vm)
    return 0, ""


def clipx(pltw, val, way):
    """ Remove all data points for which x is larger or lower than val.

        Data points for which x=val are kept.
        :param pltw: plotWin containing data
        :param val: limit value
        :param way: either '>' or '<'
        :return: an error value (=0 if no error) and an error message
                 (="" if no error). Return err=1 and msg="" to indicate
                 that nothing was done.
    """
    if not (way == '>' or way == '<'):
        return 1, "Bad parameter value"
    blkno = pltw.curvelist[0].yvinfo.blkpos
    xpos = pltw.curvelist[0].xvinfo.vidx
    xmin = pltw.blklst[blkno][xpos].min()
    xmax = pltw.blklst[blkno][xpos].max()
    if (way == '>' and val >= xmax) or (way == '<' and val <= xmin):
        # nothing to do, return
        return 0, ""
    # build a list of tuples containing unique (blkno, xpos) pair
    setlist = [(blkno, xpos)]
    ncurv = len(pltw.curvelist)
    for i in range(ncurv - 1):
        blkno = pltw.curvelist[i + 1].yvinfo.blkpos
        xpos = pltw.curvelist[i + 1].xvinfo.vidx
        if not (blkno, xpos) in setlist:
            setlist.append((blkno, xpos))
    nblk = len(setlist)
    # for each data block in setlist find either minidx or maxindx
    for i in range(nblk):
        blkno = setlist[i][0]
        xpos = setlist[i][1]
        (nvec, npt) = pltw.blklst[blkno].shape
        if way == '<':
            xmin = pltw.blklst[blkno][xpos].min()
            if val <= xmin:
                minidx = 0
            else:
                minidx = pltw.xToIdx(val, blkno, xpos)
                if minidx == None:
                    minidx = 0
            if pltw.xascending:
                newarr = np.delete(pltw.blklst[blkno], np.s_[:minidx], axis=1)
            else:
                newarr = np.delete(pltw.blklst[blkno], np.s_[minidx:], axis=1)
            pltw.blklst[blkno] = newarr
        else:  # way == '>'
            maxidx = pltw.xToIdx(val, blkno, xpos)
            if maxidx == None:
                maxidx = npt - 1
            else:
                if maxidx < npt - 2:
                    maxidx += 1
            if pltw.xascending:
                newarr = np.delete(pltw.blklst[blkno], np.s_[maxidx:], axis=1)
            else:
                newarr = np.delete(pltw.blklst[blkno], np.s_[:maxidx], axis=1)
            pltw.blklst[blkno] = newarr
    pltw.clearMarks()
    return 0, ""


def onset(pltw, curvinfo, idx1, idx2):
    """ Compute the onset of a peak.

        :param pltw: plotWin containing data
        :param curvinfo: vinfo object of the relevant curve.
        :param idx1: index of the point located on the baseline
        :param idx2: index of the point located on the peak
        :return: a tuple err, string where string contains the result
                 or an error message if err != 0.
    """
    # Algorithm
    # 1 - call linFit with direc=-1 to get the line equation at idx1
    # 2 - call linFit with direc=+1 to get the line equation at idx2
    # 3 - calculate the coordinates of the intersection of these lines
    # 4 - return the coordinates

    # If idx2 > idx1 swap them
    if idx2 < idx1:
        idx = idx1
        idx1 = idx2
        idx2 = idx
    (errmsg, pcoef1, n1, chi) = linFitProc(pltw, curvinfo, idx1, -1)
    if errmsg is None:
        (errmsg, pcoef2, n2, chi) = linFitProc(pltw, curvinfo, idx2, +1)
    if errmsg is not None:
        return 1, "Unable to compute the line equation"

    blkno = curvinfo.yvinfo.blkpos
    xpos = curvinfo.xvinfo.vidx
    ypos = curvinfo.yvinfo.vidx
    xi = (pcoef2[1] - pcoef1[1]) / (pcoef1[0] - pcoef2[0])
    yi = pcoef1[0] * xi + pcoef1[1]
    result = "The two lines meet at:\n"
    result += "xi = {0:g}\n".format(xi)
    result += "yi = {0:g}".format(yi)

    # Show the fitting lines
    siz = pltw.blklst[blkno][xpos].size
    ymin = pltw.blklst[blkno][ypos].min()
    ymax = pltw.blklst[blkno][ypos].max()
    # add the first line segment marker
    Yfit = np.polyval(pcoef1, pltw.blklst[blkno][xpos])
    x1 = pltw.blklst[blkno][xpos][idx1 - n1]
    y1 = Yfit[idx1 - n1]
    x2 = pltw.blklst[blkno][xpos][idx2]
    y2 = Yfit[idx2]
    pltw.lineList.append(lineSeg(x1, y1, x2, y2, 'red'))

    # add the second line segment marker
    Yfit = np.polyval(pcoef2, pltw.blklst[blkno][xpos])
    idx = idx1
    while Yfit[idx] < ymin and idx < idx2 - 1:
        idx += 1
    x1 = pltw.blklst[blkno][xpos][idx]
    y1 = Yfit[idx]
    x2 = pltw.blklst[blkno][xpos][idx2 + n2]
    y2 = Yfit[idx2 + n2]
    pltw.lineList.append(lineSeg(x1, y1, x2, y2, 'red'))

    pltw.displayInfo()
    pltw.plotCurves()
    return 0, result


def linEq(pltw, curvinfo, idx1, idx2):
    """ Compute the equation of the line linking two points on a curve.

        :param pltw: plotWin containing data
        :param curvinfo: vinfo object of the relevant curve.
        :param idx1: index of the first point
        :param idx2: index of the second point
        :return: a tuple (err, msg). If err=1, msg contains an error message
                 if err=0, msg contains the result of fitting.
    """
    blkno = curvinfo.yvinfo.blkpos
    xpos = curvinfo.xvinfo.vidx
    ypos = curvinfo.yvinfo.vidx
    X = pltw.blklst[blkno][xpos]
    Y = pltw.blklst[blkno][ypos]
    xm1 = pltw.markList[0].getxy()[0]
    idx1 = pltw.xToIdx(xm1, blkno, xpos)
    xm2 = pltw.markList[1].getxy()[0]
    idx2 = pltw.xToIdx(xm2, blkno, xpos)
    if idx1 < 0 or idx2 < 0 or idx1 >= X.size or idx2 >= X.size:
        return 1, "Index out of range"
    slope = (Y[idx2] - Y[idx1]) / (X[idx2] - X[idx1])
    intercept = Y[idx1] - slope * X[idx1]
    result = "Slope = {0:g}\nIntercept = {1:g}".format(slope, intercept)
    return 0, result


def shift(pltw, curvinfo, val, idx1=None, idx2=None):
    """ Add the scalar 'val' to a curve in the location defined by idx1, idx2.

        If idx1 and idx2 are None use the marker positions.
        :param pltw: plotWin containing data
        :param curvinfo: vinfo object of the relevant curve.
        :param val: the scalar value to add.
        :param idx1: the index of the first point
        :param idx2: the index of the last point
        :return: (0,"")
        """
    blkno = curvinfo.yvinfo.blkpos
    xpos = curvinfo.xvinfo.vidx
    ypos = curvinfo.yvinfo.vidx
    if idx1 is None:
        xm1 = pltw.markList[0].getxy()[0]
        idx1 = pltw.xToIdx(xm1, blkno, xpos)
    if idx2 is None:
        xm2 = pltw.markList[1].getxy()[0]
        idx2 = pltw.xToIdx(xm2, blkno, xpos)
    npt = pltw.blklst[blkno][xpos].size
    if idx1 < 0 or idx2 < 0 or idx1 >= npt or idx2 >= npt:
        return 1, "Index out of range"
    if idx1 != idx2:
        if idx1 > idx2:
            idx = idx2
            idx2 = idx1
            idx1 = idx
        for i in range(idx1, idx2 + 1):
            pltw.blklst[blkno][ypos][i] += val
    return 0, ""


def lineFit(pltw, curvinfo, idx, direc):
    """ Compute the equation of the line fitting a curve

        :param pltw: plotWin containing data
        :param curvinfo: vinfo object of the relevant curve.
        :param idx: index of the starting point.
        :param direc: must be either +1 or -1
        :return: a tuple (err, msg). If err=True, msg contains an error message
                 if err=False, msg contains the result of fitting.
    """
    blkno = curvinfo.yvinfo.blkpos
    xpos = curvinfo.xvinfo.vidx
    ypos = curvinfo.yvinfo.vidx
    ynam = curvinfo.name
    err = True
    (errmsg, pcoef, npt, chi) = linFitProc(pltw, curvinfo, idx, direc)
    if errmsg is None:
        err = False
        result = "Fitting curve {0} with a line\n".format(ynam)
        result += "Using {0:d} points\n".format(npt)
        result += "chi = {0:g}\n".format(chi)
        result += "intercept = {0:g}\nslope = {1:g}".format(pcoef[1], pcoef[0])
        # add a line segment marker to show the result
        siz = pltw.blklst[blkno][xpos].size
        ymin = pltw.blklst[blkno][ypos].min()
        ymax = pltw.blklst[blkno][ypos].max()
        Yfit = np.polyval(pcoef, pltw.blklst[blkno][xpos])
        if direc > 0:
            x1 = pltw.blklst[blkno][xpos][idx]
            y1 = Yfit[idx]
            end = idx + npt
            if end >= siz:
                end = siz - 1
            y2 = Yfit[end]
            while y2 < ymin and end > idx + 1:
                end -= 1
                y2 = Yfit[end]
            x2 = pltw.blklst[blkno][xpos][end]
        else:
            x2 = pltw.blklst[blkno][xpos][idx]
            y2 = Yfit[idx]
            ini = idx - npt
            if ini <= 0:
                ini = 0
            y1 = Yfit[ini]
            while y1 > ymax and ini < idx - 1:
                ini += 1
                y1 = Yfit[ini]
            x1 = pltw.blklst[blkno][xpos][ini]
        pltw.lineList.append(lineSeg(x1, y1, x2, y2, 'red'))
        pltw.displayInfo()
        pltw.plotCurves()
    else:
        result = errmsg
    return err, result


def linFitProc(pltw, curvinfo, idx, direc):
    """ Compute the equation of the line fitting a curve.

        :param pltw: plotWin containing data
        :param curvinfo: a curveInfo object containing the curve information.
        :param idx: the index of the point from which the fitting will start.
        :param direc: = 1 if the fitting proceed toward increasing X or equal
                      to -1 otherwise.
        :return: a tuple (errmsg, pcoef, npt, chi) where:
             - 'pcoef' contains the line parameters (intercept and slope).
             - 'npt' is the number of point used for fitting
             If no error 'errmsg' is None otherwise it contains an error message.
    """
    # Algorithm
    # 1 - Starts, in the direction given by 'direc', from 'idx' position
    #     with at least 5 points
    # 2 - Fit with a line
    # 3 - Add another point in the direction given by 'direc'
    # 4 - Return to step 2
    # Stop when enough points are used or if the fitting error exceeds
    # a given limit
    #
    errmsg = None
    if direc > 0:
        direc = 1
    else:
        direc = -1
    blkno = curvinfo.yvinfo.blkpos
    xpos = curvinfo.xvinfo.vidx
    ypos = curvinfo.yvinfo.vidx
    siz = pltw.blklst[blkno][xpos].size
    initrange = 5
    # Evaluate the maximum amplitude
    ymin = pltw.blklst[blkno][ypos].min()
    ymax = pltw.blklst[blkno][ypos].max()
    std = abs(ymax - ymin)
    if direc > 0:
        nstep = siz - idx - initrange - 1
    else:
        nstep = idx - initrange - 1
        if nstep < 0:
            nstep = 0
    chi = None
    pcoef = None
    tol = 0.002
    n = initrange
    for i in range(nstep):
        if direc > 0:
            l1 = idx
            l2 = idx + n
        else:
            l1 = idx - n
            l2 = idx
        X = pltw.blklst[blkno][xpos][l1:l2]
        Y = pltw.blklst[blkno][ypos][l1:l2]
        pcoef = np.polyfit(X, Y, 1)
        Yfit = np.polyval(pcoef, X)
        # compute the mean square error
        chi = np.sqrt(sum((Yfit - Y) ** 2) / len(Y))
        if chi / std > tol:
            break
        n += 1
    if chi is None:
        errmsg = "Unable to compute the line equation"
    return errmsg, pcoef, n, chi


def fft(pltw, vnam):
    """ Compute frequency spectrum using FFT.

        :param pltw: plotWin containing data
        :param vnam: name of the vector which will be used.
        :return: an error value (=0 is no error) and a message.
    """
    # http://glowingpython.blogspot.fr/2011/08/how-to-plot-frequency-spectrum-with.html
    # Recording of a time serie of N signals for a total time T,
    # dt = T/N
    # T and dt are the main properties of Fourier analysis.
    # A signal observed for a total time T allows a frequency resolution equal to 1/T
    # A signal observed with a sampling dt allows to get the frequencies up to 1(2.dt).
    #
    err = 1
    if pltw.parent.progpath is None:
        return "Cannot create FFT file"
    curvinfo = pltw.getCurvinfo(vnam)
    if curvinfo is None:
        return err, "No vector to process"
    Y = pltw.blklst[curvinfo.yvinfo.blkpos][curvinfo.yvinfo.vidx]
    # fft computing and normalization
    from numpy.fft import fft
    n = Y.size
    FFT = fft(Y) / n
    m = int(n / 2)
    FFT = FFT[range(m)]
    FFT = abs(FFT)
    k = np.arange(n)
    Fs = n
    T = n / Fs
    frq = k / T  # two sides frequency range
    frq = frq[range(m)]  # one side frequency range
    # Save FFT in a file
    filnam = "{0}-fft.txt".format(vnam)
    filnam = os.path.join(pltw.parent.progpath, filnam)
    try:
        np.savetxt(filnam, np.transpose([frq, FFT]), delimiter='\t')
    except PermissionError as err:
        return err, "Fail to create FFT file: {0}".format(err)
    msg = pltw.parent.loadFile(filnam)
    if msg:
        return err, "Cannot load {0}\n{1}".format(filnam, msg)
    else:
        return 0, msg



def mergeb(pltw, items):
    """ Merge two data blocks

        The data block vectors must have the same size.

    :param pltw: plotWin containing data
    :param items: list containing block numbers
    :return: a tuple (err, errmsg)
    """
    # check the parameters
    if len(items) > 2:
        return 1, "Only two blocks can be merged"
    if len(items) < 2:
        return 1, "mergeb command needs two block number"
    nb = len(pltw.blklst)
    if isNumber(items[0]):
        nb1 = int(items[0])
    if isNumber(items[1]):
        nb2 = int(items[1])
    if nb1 < 1 or nb1 > nb or nb2 < 1 or nb2 > nb:
        return 1, "Incorrect parameters"
    nb1 -= 1
    nb2 -= 1
    # check vector size
    if pltw.blklst[nb1][0].size != pltw.blklst[nb2][0].size:
        return 1, "The vectors must have the same size in both data blocks"
    nvect, nelem = pltw.blklst[nb2].shape
    for i in range(nvect):
        pltw.blklst[nb1] = np.vstack((pltw.blklst[nb1], pltw.blklst[nb2][i]))
    del pltw.blklst[nb2]
    idxshift = len(pltw.vectInfolst[nb1])
    # update pltw.vectInfolst
    for vinfo in pltw.vectInfolst[nb2]:
        vinfo.blkpos = nb1
        vinfo.vidx += idxshift
        pltw.vectInfolst[nb1].append(vinfo)
    del pltw.vectInfolst[nb2]
    # update pltw.curveInfolst
    for cinfo in pltw.curvelist:
        for vinfo in pltw.vectInfolst[nb1]:
            if cinfo.xvinfo.name == vinfo.name:
                cinfo.xvinfo = vinfo
            if cinfo.yvinfo.name == vinfo.name:
                cinfo.yvinfo = vinfo
    return 0, ""


def calculArea(plotw, curvinfo, idx1=None, idx2=None):
    """ Compute the area between a curve and x-axis.

        :param plotw: plotWin containing data
        :param curvinfo: vinfo object of the relevant curve.
        :param idx1: index of the first point
        :param idx2: index of the last point
        :return: a string containing the result.
    """
    if curvinfo is None:
        return ""
    link = True
    blkno = curvinfo.yvinfo.blkpos
    xpos = curvinfo.xvinfo.vidx
    ypos = curvinfo.yvinfo.vidx
    xnam = curvinfo.xvinfo.name
    ynam = curvinfo.yvinfo.name
    maxidx = len(plotw.blklst[blkno][xpos]) - 1
    if idx1 is None:
        idx1 = 0
    if idx2 is None:
        idx2 = maxidx
    if plotw.blklst[blkno][xpos][idx1] < plotw.blklst[blkno][xpos][idx2]:
        lowidx = idx1
        upidx = idx2
    else:
        lowidx = idx2
        upidx = idx1
    # remove data outside the limits
    dellst = list(range(0, lowidx)) + list(range(upidx + 1, maxidx + 1))
    x = np.delete(plotw.blklst[blkno][xpos], dellst)
    y = np.delete(plotw.blklst[blkno][ypos], dellst)
    a = calcArea(x, y)
    lowlim = plotw.blklst[blkno][xpos][lowidx]
    uplim = plotw.blklst[blkno][xpos][upidx]
    result = "Area between {0:g} and {1:g} = {2:g}\n\n".format(lowlim, uplim, a)
    result += "This area is defined by the curve {0}=f({1})".format(ynam, xnam)
    result += " and the x-axis"
    return result




