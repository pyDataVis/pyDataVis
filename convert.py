""" Entry point for conversion functions
"""

import os, io
import numpy as np
from PyQt5 import QtWidgets

from utils import isNumber, divideChunks, commaToDot, getSpan
from convCIF import CIF


def convSelector(parent, sel, lines, filename):
    """ Call the required conversion function according 'sel' value.

    :param parent: pyDataVis MainWindow
    :param sel: string used as selector
    :param lines: list of lines containing the text data to convert
    :param filename: name of the file name containing the data
    :return: err (True or False), msg (a string containing a message),
             savename (a string containing the name of the file in which
             the converted data will be saved).
    """
    # remove the file extension
    basename = os.path.splitext(filename)[0]
    # the saved file name is obtained by replacement of the extension by .plt
    savename = "{0}.plt".format(basename)
    infnam = os.path.split(filename)[1]
    outfnam = os.path.split(savename)[1]
    err = False
    msg = None

    if sel == 'CSV':
        title = 'CSV conversion'
        msg = convertCSV(lines, savename)
        if msg is None:
            msg = infnam + ' has been successfully used to generate ' + outfnam
        else:
            err = True

    elif sel == 'CIF':
        title = 'Generate diffraction pattern from CIF'
        msg = CIF(lines, savename)
        if msg is None:
            msg = infnam + ' has been successfully used to generate ' + outfnam
        else:
            err = True

    elif sel == 'DAT':
        title = 'DAT conversion'
        msg = convDAT(lines, savename)
        if msg is None:
            msg = infnam + ' has been successfully used to generate ' + outfnam
        else:
            err = True

    elif sel == 'PRF':
        title = 'PRF conversion'
        msg = convPRF(lines, savename)
        if msg is None:
            msg = infnam + ' has been successfully used to generate ' + outfnam
        else:
            err = True

    elif sel == 'Reshape':
        title = 'Shape conversion'
        numtab = np.array(lines)
        nelem = np.shape(numtab)
        nc, ok = QtWidgets.QInputDialog.getInt(parent, title,
                                               "Number of columns:",
                                                1, 1, nelem[0], 1)
        if ok:
            msg = convertShape(lines, nc, savename)
            if msg is None:
                 msg = infnam + ' has been successfully used to generate ' + outfnam
            else:
                err = True

    elif sel == 'Transpose':
        title = 'Transpose'
        msg = transpose(parent, savename)
        if msg is None:
            msg = infnam + ' has been successfully used to generate ' + outfnam
        else:
            err = True

    elif sel == '1D->2D':
        # Add X column containing the point number to 1D data file
        title = 'Add a X column to 1D data file'
        msg = convert2D(lines, savename)
        if msg is None:
            msg = infnam + ' has been successfully used to generate ' + outfnam
        else:
            err = True

    else:
        title = 'Data conversion'
        err = True
        msg = 'Unable to convert this data'
        savename = None

    if err:
        QtWidgets.QMessageBox.critical(parent, title, msg)
    return (err, msg, savename)



def convertCSV(flines, savename):
    """ Replace the comma or semi-column by tab in the text data in flines.

        Save the converted text to the file 'savename'.
    :param flines: List of text lines containing the data to convert.
    :param savename: name of file to which save the converted data.
    :return:  None if success otherwise return an error message.
    """
    errmsg = None
    newlines = []
    first = True
    sepchar = None
    sepdec = False

    # Replace the comma or semi-column by tab
    for line in flines:
        if line.startswith('#'):
            newlines.append(line)
        else:
            if first:
                # Try to determine what is the separator char
                r = line.find(';')
                if r > 0:
                    sepchar = ';'
                else:
                    r = line.find(',')
                    if r > 0:
                        sepchar = ','
                if sepchar is None:
                    errmsg = "Unable to guess separator"
                    break
                if sepchar == ';':
                    r = line.find(',')
                    if r > 0:
                        r = line.find('.')
                        if r < 0:
                            # it is guessed that if there is no dot the decimal
                            # separator is comma. Put 'sepdec'=True to indicate
                            # that comma should be replaced by dot.
                            sepdec = True
                first = False
            if sepdec:
                line = commaToDot(line)
            newlines.append(line.replace(sepchar, '\t'))

    # Save converted data in a text file
    if errmsg is None:
        fo = open(savename, 'w')
        fo.write("\n".join(newlines))
        fo.close()
    return errmsg



def convert2D(flines, savename):
    """ Add a new column containing the point number to 1D data files.

    :param flines: List of text lines containing the data to convert.
    :param savename:  name of file to which save the converted data.
    :return: None if success otherwise return an error message.
    """
    errmsg = None
    newlines = []
    header = []
    idx = 0

    for n, line in enumerate(flines):
        if line.startswith('#'):
            # Add comment lines in the header without modification.
            line = line + '\n'
            header.append(line)
        else:
            line.strip()
            if len(line):
                # Replace the comma by dot
                line = commaToDot(line)
                line = str(idx) + "\t" + line
                newlines.append(line)
                idx += 1
    # Save converted data in a text file
    if errmsg is None:
        fo = open(savename, 'w')
        fo.write("\n".join(header))
        fo.write("\n".join(newlines))
        fo.close()
    return errmsg


def convertUTF16(filename, savename):
    """ Convert the file 'filename' in UTF8.

    :param filename: Name of the file to convert.
    :param savename:  Save the converted data to the file 'savename'.
    :return: None if success otherwise return an error message.
    """
    errmsg = None
    fi = io.open(filename, 'r', encoding = 'utf-16')
    fo = io.open(savename, 'w', encoding = 'utf-8')
    for line in fi.readlines():
        fo.write(line)
    fo.close()
    fi.close()
    return errmsg



def convDAT(lines, savename):
    """ Convert .DAT diffraction file format in a standard text file

    :param lines: List of the text lines containing the data
    :param savename: Save the converted data to the file 'savename'
    :return: None if success otherwise return an error message.
    """
    # Remove empty lines
    newlines = [ lin for lin in lines if lin ]
    # Remove comment lines (starting with #)
    lines = [ lin for lin in newlines if not lin.startswith('#')]
    # Remove multiple spaces
    newlines = [ " ".join(lin.split()) for lin in lines]
    # The first line should contain 2theta start, step and final value
    params = newlines[0].split()
    errmsg = "Unknown file format"
    if isNumber(params[0]):
        start = float(params[0])
        if isNumber(params[1]):
            step = float(params[1])
            if isNumber(params[2]):
                stop = float(params[2])
                if stop > start:
                    errmsg = None
    if errmsg is not None:
        return errmsg

    Ilst = [lin.split() for lin in newlines[1:]]
    # Flatten the list of list
    fIlst = [item for sublist in Ilst for item in sublist]
    lines = []
    for j, I in enumerate(fIlst):
        x = start + j * step
        lin = "{0}\t{1}".format(x, I)
        lines.append(lin)

    # Save the new list in a file
    outfile = open(savename, 'w')
    outfile.write("\n".join(lines))
    return errmsg



def convPRF(lines, savename):
    """ Convert a PRF file generated by Fullprof in a standard text file.

        Save the converted data in the file 'filename'.

    :param lines: list of the text lines containing the PRF data
    :param savename: name of file to which converted data will be saved.
    :return: None if success otherwise return an error message.
    """

    err = 0
    if not any(" 2Theta" in lin for lin in lines) or len(lines) < 7:
        err = 1
    nl = len(lines)
    nitems = lines[1].split(' ')
    nitems = [x for x in nitems if x]
    if not isNumber(nitems[1]):
        err = 1
    else:
        npt = int(nitems[1])
        if npt > nl:
            err = 1
    if err:
        return "Unknown file format"
    
    startidx = [idx for idx, s in enumerate(lines) if " 2Theta" in s][0] + 1
    errmsg = None
    newlines = []
    # Add a # at the beginning of the first line
    newlines.append('#' + lines[0])
    newlines.extend(["# 2Theta\tYobs\tYcal\tYobs_Ycal"])

    # For each line keeps only the 4 first items
    for l, line in enumerate(lines):
        if l >= startidx and l < npt+startidx:
            items = line.split('\t')
            line = [items[i] for i in range(4)]
            newlines.append("\t".join(line))

    # Save the new list in a file
    outfile = open(savename, 'w')
    outfile.write("\n".join(newlines))
    return errmsg



def transpose(parent, savename):
    """ Transpose the data of the active plotWin.

    :param parent: pyDataVis MainWindow
    :param savename: name of the file where data are saved
    :return: an error message if there is no active window.
    """
    errmsg = None
    wlist = parent.mdi.subWindowList()
    if len(wlist) == 0:
        errmsg = "No data to process"
    else:
        pltw = wlist[-1].widget()
        numtab = pltw.blklst[0]
        newlines = numtab.tolist()
    # Save converted data in a text file
    if errmsg is None:
        fo = open(savename, 'w')
        for line in newlines:
            # Convert the list of floats into a list of strings
            strlin = [str(x) for x in line]
            # Convert the list into a string with \t separators
            strlin = '\t'.join(strlin)
            # Append a \n at the end and write in the file
            fo.write("{0}\n".format(strlin))
        fo.close()
    return errmsg



def convertShape(lines, ncol, savename):
    """ Reshape the text data in lines in 'ncol' columns

        Of course the number of elements in lines should be an exact
        multiple of 'ncol'.

    :param lines: list of the text lines containing the data.
    :param ncol: number of columns.
    :param savename: Save the converted data to the file 'savename'.
    :return: None if success otherwise return an error message.
    """
    errmsg = None
    nlold = len(lines)
    lin = lines[0].split()
    ncold = len(lin)
    nelem = ncold * nlold
    if nelem % ncol:
        return "Incompatible dimension"
    listlist = [lin.split() for lin in lines]
    # Flatten the list of list
    flatlist = [item for sublist in listlist for item in sublist]
    # Divide the flatten list in chunk of ncol elements
    newlines = list(divideChunks(flatlist, ncol))

    # Save converted data in a text file
    if errmsg is None:
        fo = open(savename, 'w')
        for line in newlines:
            str = '\t'.join(line)
            fo.write("{0}\n".format(str))
        fo.close()
    return errmsg



def convertToAbs(IRspec):
    """  Convert an IR spectrum in absorbance

         Use: A = 2 -log10(%T)
           or A = -log10(T)

    :param IRspec: a curve (2 vectors) containing an IR spectrum in transmittance.
    :return: a tuple (err, msg) where err = True if an error occurred,
             and msg contains an error message.
    """
    msg = None
    err = False
    if IRspec[1].min() < 0.0 or IRspec[1].max() > 100.0:
        msg = 'Transmittance data out of range'
    Tspan = getSpan(IRspec[1])
    if IRspec[1].max() > 1.0 and Tspan > 1.0:
       IRspec[1] = 2.0 - np.log10(IRspec[1])
    else:
        IRspec[1] = -1.0 * np.log10(IRspec[1])
    return (err, msg)


def convertToTrans(IRspec):
    """ Convert an IR spectrum in transmittance

        Use: %T = 10^(2-A)

    :param IRspec: a curve (two vectors) containing an IR spectrum in absorbance.
    :return: a tuple (err, msg) where err = True if an error occurred,
             and msg contains an error message.
    """
    msg = None
    err = False
    if IRspec[1].min() < 0.0:
        msg = 'Absorbance data out of range'
    IRspec[1] = np.power(10, (2.0 - IRspec[1]) )
    return (err, msg)

