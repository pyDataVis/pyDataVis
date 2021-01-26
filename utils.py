# General purpose functions
#
import os
import csv
import math
from datetime import date
import numpy as np
import requests


def isNumber(s):
    """ Return True if 's' can be converted in a float.

    :param s: the value to test
    :return: a boolean
    """
    try:
        float(s)
        return True
    except ValueError:
        return False


def isNumeric(list):
    """ Return True if all elements in 'list' are numeric.

    :param list: the list to test
    :return: a boolean
    """
    if not len(list):
        return False
    ok = True
    for item in list:
        if not isNumber(item):
            ok = False
            break
    return ok


def isNotNumeric(list):
    """  Return True if at least one element in 'list' is not numeric.

    :param list: the list to test
    :return: a boolean
    """
    return not (isNumeric(list))


def isNumData(nstring, sep=None):
    """  Return True if 'nstring' contains only numeric data.

         Convert the string in list and call isNumeric.

    :param nstring: the string to test
    :return: a boolean
    """
    if isNumber(nstring):
        return True
    if sep is None:
        # Try to guess the element separator
        try:
            dialect = csv.Sniffer().sniff(nstring)
        except csv.Error:
            sep = None
        else:
            sep = dialect.delimiter
    if sep is None:
        return isNumeric(nstring)
    items = nstring.split(sep)
    if sep == ' ':
        # Remove empty elements (case of multiple space separators)
        items = [x for x in items if x]
    return isNumeric(items)


def commaToDot(s):
    """  Return s where all commas have been replaced by dots.

    :param s: the string to test
    :return: the modified string.
    """
    s = s.replace(',', '.')
    return s


def round_to_n(x, n):
    """ Round the number x to n significant figures

    :param x: the number to round
    :param n: the number of significant figures
    :return: the rounded number

    :examples
    round_to_n(0.045624, 3) == 0.0456
    round_to_n(0.45624, 3) == 0.456
    round_to_n(1.45624, 2) == 1.5
    round_to_n(14.5624, 4) == 14.56
    """
    if not x:
        return 0
    power = -int(math.floor(math.log10(abs(x)))) + (n - 1)
    factor = (10 ** power)
    x = round(x * factor) / factor
    return x


def findFile(name, path):
    """ Return the path of the first file which name is 'name' inside the folder 'path'.

    :param name: the name of the file
    :param path: the path of the folder where the file is assumed to be.
    :return: the path or None is the file is not found.
    """ 
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)
    return None


def checkWeb():
    """ Check Internet connection

    :return: True is connected, False otherwise.
    """
    try:
        # IP of Google LLC (google.com)
        r = requests.get('http://216.58.192.142')
    except requests.ConnectionError as err:
        return False
    if r.status_code == 200:
        return True
    return False


def checkURL(url):
    """ Check if 'url' is valid and exists on the internet.

    :param url: URL to test
    :return: True if URL is valid and exists on the internet.
    """
    try:
        r = requests.get(url)
        # URL is valid and exists on the internet
        return True
    except requests.ConnectionError as err:
        # URL does not exist on Internet
        pass
    return False


def cpyFromURL(url, filename):
    """ Create a copy of the file in 'url'

    :param url: URL of the file to copy
    :param filename: name of the file to create
    :return: True if success.

    """
    if not checkURL(url):
        return False
    r = requests.get(url, allow_redirects=True)
    try:
        open(filename, 'wb').write(r.content)
    except IOError as err:
        return False
    return True



def textToBlocks(lines, sep):
    """ Convert the numeric data in lines in a list of data block

        Each data block is separated from the next by two empty lines.
        Each block can be preceded by a header, a non numeric line
        containing the vector names.
        If the number of elements in each line is not the same this
        trigger a IndexError and a return with empty blocks and headers.

    :param lines: list of strings containing data.
    :param sep: a character, the column separator; if = 0 means 1D data
    :return: a tuple with a list of data blocks and a list of associated headers.
    """
    blocks = []
    block = []
    headers = []
    header = []
    newblk = True
    emptylin = 0
    nl = 0
    try:
        for line in lines:
            line = str(line.strip())
            if len(line):  # if the line is not empty
                # test if the line contains only numeric items
                if not isNumData(line, sep):
                    header.append(line)
                else:
                    if sep is None:
                        if newblk:
                            block.append([])
                            newblk = False
                        block[0].append(float(line))
                    else:
                        items = line.split(sep)
                        if sep == ' ':
                            # Remove empty elements
                            # (case of multiple space separators)
                            items = [x for x in items if x]
                        nc = 0
                        for item in items:
                            if newblk:  # for a new block
                                # create a new empty list for storing
                                # column elements
                                block.append([])
                            block[nc].append(float(item))
                            nc += 1
                            nl += 1
                        if nc != 0:
                            newblk = False
            else:  # it is an empty line
                emptylin += 1
                if emptylin > 1:  # is it a new block ?
                    if block != [] and block[0] != []:
                        blocks.append(block)  # append the last block if any
                        headers.append(header)
                    emptylin = 0
                    newblk = True
                    block = []
                    header = []
        if block != [] and block[0] != []:  # append the last block if it
            blocks.append(block)  # was not done
            headers.append(header)
    except (IndexError) as e:
        blocks = []
        headers = []
    return blocks, headers


def JcampDX(textlines):
    """ Decode IR or MS data from text in JCamp-DX format

        This format is only suitable for spectra from spectroscopy experiments:
        http://cedadocs.ceda.ac.uk/999/1/JCAMP-DX_format.html

    :param textlines:  list of lines containing the text data
    :return: a tuple containing (errmsg, data, headers)
    """
    Xdata = []
    Ydata = []
    data = []
    header = []
    errmsg = ""
    nl = 0
    head = True
    dform = None
    deltaX = 0.0
    firstX = 0.0
    lastX = 0.0
    npoints = 0

    try:
        for line in textlines:
            lin = line.strip()
            if len(lin):
                # check that first line contains: ##TITLE=
                if nl == 0:
                    if lin.find('##TITLE=') == -1:
                        errmsg = 'Not a JCamp-DX file'
                # check that second line contains: ##JCAMP-DX=
                elif nl == 1:
                    if lin.find('##JCAMP-DX=') == -1:
                        errmsg = 'Not a JCamp-DX file'
                else:
                    if head:
                        if lin.find('##DELTAX=') != -1:
                            items = lin.split('=')
                            deltaX = float(items[1])
                        elif lin.find('##FIRSTX=') != -1:
                            items = lin.split('=')
                            firstX = float(items[1])
                        elif lin.find('##LASTX=') != -1:
                            items = lin.split('=')
                            lastX = float(items[1])
                        elif lin.find('##NPOINTS=') != -1:
                            items = lin.split('=')
                            npoints = int(items[1])
                        # store lines in header with # prefix if needed
                        if lin[0] == '#':
                            newlin = "{0}".format(line)
                        else:
                            newlin = "#{0}".format(line)
                        header.append(newlin)
                        if lin.find('##XYDATA=(X++(Y..Y))') != -1:
                            head = False
                            dform = 'X++(Y..Y)'
                        elif lin.find('##PEAK TABLE=') != -1:
                            head = False
                            dform = 'XY..XY'
                    else:
                        if lin.find('##END=') != -1:
                            break
                        if dform == None:
                            errmsg = 'Unknown file format'
                        else:
                            if dform == 'XY..XY':
                                items = lin.replace(' ',',')
                                items = items.rsplit(',')
                                # convert string list in float list
                                XY = [ float(i) for i in items ]
                                # even index are X and odd index are Y
                                X = [ XY[i] for i in range(len(XY)) if i % 2 == 0 ]
                                Y = [ XY[i] for i in range(len(XY)) if i % 2 == 1 ]
                            if dform == 'X++(Y..Y)':
                                if deltaX == 0.0:
                                    if npoints != 0:
                                        deltaX = (lastX - firstX + 1)/npoints
                                if deltaX == 0.0:
                                    errmsg = 'DELTAX not found'
                                else:
                                    items = lin.rsplit(' ')
                                    n = len(items) - 1
                                    X0 = float(items[0])
                                    Xn = X0 + n * deltaX
                                    X = np.linspace(X0, Xn, num=n, endpoint=False).tolist()
                                    Y = [ float(i) for i in items[1:] ]
                            if errmsg == "":
                                Xdata.extend(X)     # extend Xdata list with X elems
                                Ydata.extend(Y)     # extend Ydata list with Y elems
            if errmsg != "":
                break
            nl += 1
        if errmsg == "":
            data.append(Xdata)
            data.append(Ydata)

    except (ValueError) as e:
        errmsg = str(e)
    return (errmsg, data, header)



def textToData(text, sep):
    """ Convert the text in 'text' in data blocks.

    :param text: list of lines containing the text data
    :param sep: a character, the column separator; if = 0 means 1D data
    :return: a tuple (errmsg, blocks, headers) where
             - errmsg contains an error message (errmsg = None if no error)
             - blocks contains a list of data blocks (numpy arrays)
             - headers contains a list of headers
    """
    blocks = None
    headers = None
    errmsg = ""
    try:
        blocks, headers = textToBlocks(text, sep)
    except (ValueError) as err:
        errmsg = err
    return (errmsg, blocks, headers)



def dataToFile(filename, blklst, headers):
    """
       Save the list of numpy array 'blklst' in a text file

       Return a tuple (errno, errmsg) where
       - errno is an error code = 0 if success
       - errmsg is the error message
    """
    if blklst == None or len(blklst) == 0:
        return (1, "bad parameters")
    filnam = str(filename)
    try:
        fo = open(filnam, 'w')
        for i, nparray in enumerate(blklst):
            fo.write(headers[i])
            (nvec, npt) = np.shape(nparray)
            for r in range(npt):
                lin = ""
                for c in range(nvec):
                    lin += "{0:g}".format(nparray[c][r])
                    if c < nvec-1: lin +='\t'
                lin+= '\n'
                fo.write(lin)
            if i < len(blklst)-1:
                fo.write('\n\n')            # to mark the next block
        fo.close()
        return (0, "")
    except (PermissionError, ValueError) as err:
        return (2, str(err))



def arrayToString(nparray, vectnames=None):
    """  Convert the numpy array 'nparray' in a python string

    :param nparray: the nparray to convert in string
    :param vectnames: a string containing the vector names
    :return: a string containing the nparray converted in text
    """
    string = ""
    if vectnames is not None:
         string = "{0}\n".format(vectnames)
    (ncol, nrow) = nparray.shape
    for r in range(nrow):
        lin = ""
        for c in range(ncol):
            lin += str(nparray[c][r])
            if c < ncol-1:
                lin +='\t'
        lin+= '\n'
        string += lin
    return string


def listToArray(numlst):
    """ Convert a list of list into a numpy array

        Non numeric elements will be set to zero.
        Each sublist should contain the same number of elements and 
        the sublists are assumed to be the columns (X & Y values).

    :param numlst: the list to be converted
    :return: a numpy array or None if an error is detected.
    """

    if numlst == None:
        return None
    if len(numlst) < 1:
        return None
    nvect = len(numlst[0])
    nelem = len(numlst)
    A = np.zeros((nelem, nvect))
    for r in range(0, nelem):
        for c in range(0, nvect):
            try:
                if isNumber(numlst[r][c]):
                    A[r][c] = float(numlst[r][c])
            except IndexError:
                print("The number of elements in rows should be the same !")
                return None
    return A



""" About yield 
    The yield statement suspends function’s execution and sends a value back
    to the caller, but retains enough state to enable function to resume where
    it is left off. When resumed, the function continues execution immediately
    after the last yield run. This allows its code to produce a series of 
    values over time, rather than computing them at once and sending them
    back like a list.
"""

def divideChunks(lst, n):
    """Yield successive n-sized chunks from the list lst.

    :param lst: the list to divide
    :param n: the number of items in each chunk
    :return: each successive chunk
    """
    # looping till the length of lst
    for i in range(0, len(lst), n):
        yield lst[i:i + n]



def calcArea(X, Y, link=False):
    """ Calculation of the area under a curve Y=f(X)

    :param X: np array containing x coordinates of the curve
    :param Y: np array containing y coordinates of the curve
    :param link: If link=True remove the area between the baseline and X-axis.
    :return: the area under the curve Y=f(X). If X and Y have not the same
             dimension returns None.
    """
    n = len(X)
    if len(Y) != n:
        return None
    a = np.trapz(Y, X)
    if link:
        # remove the area between the baseline and X-axis
        dx = X[n - 1] - X[0]
        dy = Y[0] + (Y[n - 1] - Y[0]) / 2.0
        a -= dx * dy
    return a


def shrinkRows(A, factor, aver=True):
    """ Reduce the number of rows in array 'A' by a factor 'factor'.

        If the 'aver' = True replace in each element by the average of
        the 'factor' neighboring values.
        It 'aver = False keep only the first value of a group of 'factor' rows.
        The 'factor' parameter should be less than 10.

    :param A: The array to transform
    :param factor: The reduction factor
    :param aver: averaging flag
    :return: The reduced array if success; otherwise returns None
    """
    if factor < 2 or factor > 10:
        return None
    else:
        A = np.array(A)
        (ncol, nrow) = A.shape
        newl = nrow / factor
        if nrow - newl * factor > 0:
            newl += 1
        newl = int(newl)
        As = np.zeros( (ncol, newl) )
        l = lr = 0
        while lr < newl:
            for c in range(ncol):
                if aver:
                    i = 0
                    som = 0.0
                    while i < factor and l+i < nrow:
                        som += A[c][l+i]
                        i += 1
                    som /= i
                else:
                    som = A[c][l]
                As[c][lr] = som
            l += factor
            lr += 1
    return As



def exportToVeusz(filename, blklst, vnamlst, plotlst, lablst=None):
    """  Export the plot in 'filename' using Veusz format.

    :param filename: name of the file to which data will be exported.
    :param blklst: list of data blocks
    :param vnamlst: list of vector names
    :param plotlst: list of the plotting commands
    :param lablst: list of the axis labels
    :return: a tuple containing an error code (0 if success) and an error message ("" if no error).
    """
    if len(blklst) == 0 or len(vnamlst) == 0:
        return (1, "bad parameters")
    colors = ['black', 'blue', 'green', 'red', 'darkred', 'gray', 'magenta', 'cyan' ]
    lines = []
    lines.append("#Generated by pyDataVis on {0}\n".format(date.today()))
    lines.append("\n")
    lines.append("AddImportPath(u'/Users/pierre/Downloads')\n")
    iv = 0
    npm = 0
    for nparray in blklst:
        (nvec, npt) = nparray.shape
        if npt > npm:
            npm = npt
        for vect in range(nvec):
            line = "ImportString(u'{0}(numeric)','''\n".format(vnamlst[iv])
            lines.append(line)
            for val in range(npt):
                lines.append(str(nparray[vect][val]) + "\n")
            lines.append("''')\n")
            iv += 1

    lines.append("Set('width', u'10cm')\n")
    lines.append("Set('height', u'10cm')\n")
    lines.append("Add('page', name='page1', autoadd=False)\n")
    lines.append("To('page1')\n")
    lines.append("Set('width', u'10cm')\n")
    lines.append("Set('height', u'10cm')\n")

    lines.append("Add('graph', name='graph1', autoadd=False)\n")
    lines.append("To('graph1')\n")
    params = plotlst[0][5:]
    cnames = params.split(',')
    # X axis
    lines.append("Add('axis', name='x', autoadd=False)\n")
    lines.append("To('x')\n")
    if lablst is not None:
        label = lablst[0]
    else:
        label = cnames[0]
    lines.append("Set('label', u'{0}')\n".format(label))
    lines.append("Set('Label/font', u'Arial')\n")
    lines.append("Set('Label/size', u'14pt')\n")
    lines.append("Set('Label/bold', True)\n")
    lines.append("Set('TickLabels/font', u'Arial')\n")
    lines.append("Set('TickLabels/size', u'12pt')\n")
    lines.append("To('..')\n")
    # Y axis
    lines.append("Add('axis', name='y', autoadd=False)\n")
    lines.append("To('y')\n")
    if lablst is not None:
        label = lablst[1]
    else:
        label = cnames[1]
    lines.append("Set('label', u'{0}')\n".format(label))
    lines.append("Set('Label/font', u'Arial')\n")
    lines.append("Set('Label/size', u'14pt')\n")
    lines.append("Set('Label/bold', True)\n")
    lines.append("Set('TickLabels/font', u'Arial')\n")
    lines.append("Set('TickLabels/size', u'12pt')\n")
    lines.append("To('..')"+ "\n")
    # XY plots
    ncol = len(colors)
    ncurv = len(plotlst)
    if ncurv > ncol-1:
        ncurv = ncol-1
    for i in range(ncurv):
        params = plotlst[i][5:]
        cnames = params.split(',')
        lines.append("Add('xy', name='{0}', autoadd=False)\n".format(cnames[1]))
        lines.append("To('{0}')\n".format(cnames[1]))
        if npm > 40:
            lines.append("Set('marker', u'none')\n")
        lines.append("Set('color', u'{0}')\n".format(colors[i+1]))
        lines.append("Set('xData', u'{0}')\n".format(cnames[0]))
        lines.append("Set('yData', u'{0}')\n".format(cnames[1]))
        lines.append("Set('key', u'{0}')\n".format(cnames[1]))
        lines.append("To('..')\n")
    # Add key
    lines.append("Add('key', name='key1', autoadd=False)\n")
    lines.append("To('key1')\n")
    lines.append("Set('Text/font', u'Arial')\n")
    lines.append("Set('horzPosn', 'centre')\n")
    lines.append("Set('vertPosn', 'top')\n")
    lines.append("Set('horzManual', 0.0)\n")
    lines.append("Set('vertManual', 0.0)\n")
    lines.append("To('..')\n")
    lines.append("To('..')"+ "\n")
    lines.append("To('..')"+ "\n")

    ufilnam = str(filename)
    try:
        fo = open(ufilnam, 'w')
        for line in lines:
            fo.write(line)
        fo.close()
    except (ValueError) as e:
        return (2, str(e))
    return (0, "")



# -------------- Filtering data ------------------
#
def Mirror(data):
    """
       Extend array 'data' with a mirror image to the left and right

       Input parameters:
       - data => data as a 1D numpy array
       Returns extended data as a numpy array

       Invoke like:
       extented = mirror(<org data>)
    """
    firstval=data[0]
    lastval=data[len(data)-1]

    window_size = len(data)
    half_window = (window_size-1) // 2        # // is truncating division

    #left extension: f(x0-x) = f(x0)-(f(x)-f(x0)) = 2f(x0)-f(x)
    #right extension: f(xl+x) = f(xl)+(f(xl)-f(xl-x)) = 2f(xl)-f(xl-x)
    leftpad = np.zeros(half_window) + 2 * firstval
    rightpad = np.zeros(half_window) + 2 * lastval
    leftchunk = data[1:1+half_window]
    leftpad = leftpad-leftchunk[::-1]
    rightchunk = data[len(data)-half_window-1:len(data)-1]
    rightpad = rightpad-rightchunk[::-1]
    data = np.concatenate((leftpad, data))
    data = np.concatenate((data, rightpad))
    return np.array(data)



def MovAver(data, n):
    """ The moving average filter operates by averaging 'n' points from the
        input data to produce each point in the output data.

    :param data: the input data to smooth.
    :param n: an odd integer.
    :return: the filtered data in a numeric array of the same size than input.
    """
    try:
        n = abs(int(n))
    except ValueError:
        raise ValueError("n have to be of type int (float will be converted).")
    if n % 2 != 1 or n < 1:
        raise TypeError("n must be a positive odd number, was: %d" % n)

    av = np.array(data)
    if n < 3:
        return av        # if n = 1 there is nothing to do

    w = n // 2
    npt = len(data)
    m = npt // 2
    exdata = Mirror(data)

    for i in range(npt):
        s = np.sum(exdata[m+i-w:m+i+w+1])
        av[i] = s / float(n)
    return av



def getSpan(V):
    """ Return the span of vector V

    :param V: 1D numpy array containing the vector V
    :return: a float, containing the span of V
    """
    if V.min() * V.max() > 0.0:
        span = abs(V.max() - V.min())
    else:
        span = abs(V.max()) + abs(V.min())
    return span




# -------------- Modifing array ------------------

def exchRow(A,i,j):
    """
       Exchange the rows i and j in the numpy array 'A'

       Returns the modified numpy array
    """
    if i == j:
        return A
    nrows, ncols = np.shape(A)
    if i < 0 or j < 0 or i > nrows-1 or j > nrows-1:
        return A
    itmp = A[i,:].copy()
    A[i,:] = A[j,:]
    A[j,:] = itmp.copy()
    return A


def exchCol(A,i,j):
    """
       Exchange the columns i and j in the numpy array 'A'

       Returns the modified numpy array
    """
    if i == j:
        return A
    nrows, ncols = np.shape(A)
    if i < 0 or j < 0 or i > ncols-1 or j > ncols-1:
        return A
    itmp = A[:,i].copy()
    A[:,i] = A[:,j]
    A[:,j] = itmp.copy()
    return A



def sortArr(A, xpos):
    """ Sort rows by ascending values along vector 'xpos'

        Call .argsort() on the column 'xpos' to sort, which gives an array of
        row indices that sort 'xpos' column which are passed as an index to
        the original array.
        Returns the modified numpy array
    """
    At = np.transpose(A)
    As = At[At[:, xpos].argsort()]
    At = np.transpose(As)
    return At


def compare(it1, it2):
    """ Return 1 if it1 > it2, 0 if it1 = it2 and =1 if it1 < it2

        This function replace cmp(it1[0], it2[0]) which was used in Python 2
        :param it1:
        :param it2:
        :return:
    """
    return (it1[0] > it2[0]) - (it1[0] < it2[0])



def delDupliX(A, xpos):
    """
       Remove the extra rows which have the same X in the numpy array 'A'

       Sort rows by ascending values of the first column, then when two
       rows start with the same value (supposed to be X) they are merged.
       Returns the modified numpy array.
    """
    As = sortArr(A, xpos)
    nrows, ncols = np.shape(As)
    # Find unique sorted values for x
    xnew, indices, counts = np.unique(As[xpos], return_index=True, return_counts=True)
    newnpt = xnew.size
    Ar = np.zeros((nrows, newnpt))
    Ar[xpos] = xnew
    for r in range(nrows):
        if r != xpos:
            Ar[r] = As[r][indices]
    return Ar



def rms(X):
    """
        Calculate the root mean square (RMS) of the array X
        :param X: a numpy array
        :return: the RMS value
    """
    return np.sqrt(np.mean(X**2))


def pp(X):
    """
        Calculate the peak-to-peak (pp) value of the array X
        :param X:
        :return: the pp value.
    """
    return X.max() - X.min()
