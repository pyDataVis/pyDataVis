# Functions for processing N2 adsorption isotherms
#
import datetime
import numpy as np
from scipy import stats
from collections import namedtuple

gas2liq = 0.001545


def findBETrange(iso):
    """  Extract from isotherm the data in BET range (0.04 < Pr < 0.30).

    :param iso: Curve (2 vectors) containing the adsorption isotherm.
    :return: Return the iso range required and a error message.
    """
    errmsg = ''
    # find best range
    (nvec, npt) = np.shape(iso)
    istart = 0
    iend = npt-1
    for i in range (npt):
        if iso[0][i] > 0.03:
            istart = i
            break
    for i in range (istart+1, npt):
        # stop when Pr > 0.30
        if iso[0][i] > 0.30:
        # stop when Va(1-Pr) is no more increasing with Pr
        # if iso[1][i]*(1-iso[0][i]) < iso[1][i-1]*(1-iso[0][i-1]):
            iend = i
            break
    n = iend - istart + 1
    if n < 7:
        errmsg = 'Not enough data points in BET range (0.04 < Pr < 0.30)'
    else:
        lst = np.hsplit(iso, np.array([istart, iend+1]))
        BET = lst[1]
        return (BET, errmsg)



def calcBET(BET):
    """ Compute a linear regression on the BET transform.

    :param BET: 3D array which contains relative pressure [0], adsorbed
                volume [1] and BET transform [2].
    :return: The results of the BET computation (r_val is the correlation
             coefficient).
    """
    slope, intercept, r_val, p_val, std_err = stats.linregress(BET[0],BET[2])
    C = slope / intercept + 1
    Vm = 1 / (intercept * C)
    SBET = 4.3525 * Vm
    return (slope, intercept, r_val, std_err, C, Vm, SBET)


def processBET(iso):
    """ Return the optimum BET values.

        Find, in the relative pressure range 0.04 - 0.30, a window of at least
        seven data points, giving the best correlation coefficient.

    :param iso: Curve (2 vectors) containing the adsorption isotherm.
    :return: errmsg (an error message), bestprm (the BET parameters giving the
             best correlation coefficient), Pri (initial relative pressure),
             Prf (final relative pressure).
    """
    reslist = []
    bestprm = None
    Pri = Prf = None
    BETprop = namedtuple('BETprop', 'w i slope intercept cc std_err C Vm SBET')
    (BET, errmsg) = findBETrange(iso)
    if not errmsg:
        (nvar, npt) = np.shape(BET)
        # Append a row of zeros:
        BET = np.vstack((BET, np.zeros((1, BET.shape[1]))))
        # Calculate BET transform
        for i in range(npt):
            BET[2][i] = 1/(BET[1][i]*(1/BET[0][i]-1))
        bestprm = None
        minpt = 7   # number minimum of points needed to compute SBET
        for w in range(minpt, npt+1):
            for i in range(npt-w+1):
                lst = np.hsplit(BET, np.array([i, i+w+1]))
                RBET = lst[1]
                (slope, intercept, cc, std_err, C, Vm, SBET) = calcBET(RBET)
                res = [w, i, slope, intercept, cc, std_err, C, Vm, SBET]
                reslist.append(res)
                # store the best result in bestprm
                if intercept > 0.0:
                    if bestprm is None:
                        bestprm = BETprop(w, i, slope, intercept, cc, std_err, C, Vm, SBET)
                    else:
                        if cc > bestprm.cc:
                            bestprm = BETprop(w, i, slope, intercept, cc, std_err, C, Vm, SBET)
        if bestprm is not None:
            # save results in a text file
            fo = open("logfile.txt", 'a')
            # write current date and time from now variable
            headtxt = "#\n#\n#%s\n" % datetime.datetime.now()
            headtxt += "#Results of computation of BET parameters\n"
            headtxt += '#w\t i\t slope\t intercept\t r_val\t std_err\t C\t Vm\t SBET\n'
            fo.write(headtxt)
            for lin in reslist:
                strlst = []
                strlst.append("{0}".format(lin[0]))
                strlst.append("{0}".format(lin[1]))
                for n in lin[2:]:
                    strlst.append("{0:E}".format(n))
                strlin = '\t'.join(strlst)
                fo.write("{0}\n".format(strlin))
            fo.close()
            Pri = BET[0][bestprm.i]
            Prf = BET[0][bestprm.i + bestprm.w - 1]
        else:
            errmsg = 'Unable to calculate BET parameters'
    return (errmsg, bestprm, Pri, Prf)


def BET(iso, ads):
    """ Compute BET from an N2 adsorption isotherm (P/Po, Va)

    :param iso: Curve (2 vectors) containing the adsorption isotherm.
    :param ads: String indicating the adsorbent. Currently only nitrogen
                (ads='N2') is implemented.
    :return: a tuple (err, msg) where err = True if an error occurred,
             and msg contains either the error message or the results.
    """
    errmsg = None
    err = False
    if ads != 'N2':
        err = True
        errmsg = "Only nitrogen adsorption is implemented"
        return err, errmsg

    if iso[0].min() < 0.0 or iso[0].max() > 1.0:
        errmsg = 'Relative pressure out of range'
    if errmsg is None:
        if iso[1].min() < 0.0 or iso[1].max() > 5000:
            errmsg = 'Adsorbed volume out of range'
    if errmsg is not None:
        return err, errmsg

    (msg, bestprm, Pri, Prf) = processBET(iso)
    if msg:
        err = True
    else:
        msg =  'BET Surface Area Report \n\n'
        msg += 'Best fitting obtained for :  {} data points\n'.format(bestprm.w)
        msg += '  First relative pressure : {0:6.3f} \n'.format(Pri)
        msg += '   Last relative pressure : {0:6.3f} \n\n'.format(Prf)
        msg += '         BET Surface Area : {0:7.2f} m2/g\n'.format(bestprm.SBET)
        msg += '                        C : {0:5.1f} \n'.format(bestprm.C)
        msg += '                    Slope :  {0:5.4f} g/cm3\n'.format(bestprm.slope)
        msg += '              Y-Intercept :  {0:4.5f} g/cm3\n'.format(bestprm.intercept)
        msg += '                       Vm :  {0:6.3f} cm3/g\n'.format(bestprm.Vm)
        msg += '  Correlation Coefficient :  {0:4.5f} \n\n'.format(bestprm.cc)
        if iso[0].max() > 0.98:
            msg += '  Adsorbed volume at Psat : {0:7.2f} mL/g\n'.format(iso[1].max())
            msg += '              Pore volume : {0:6.3f} mL/g \n\n'.format(iso[1].max() * gas2liq)
    fo = open("logfile.txt", 'a')
    fo.write("\n{0}".format(msg))
    fo.close()
    msg += 'These results are saved in logfile.txt'
    return err, msg


#- PSD --------------------------------------------------------------

def KelvinRadius(Pr, F):
    """ Return the Kelvin radius according to the relative pressure Pr.

        The returned value is valid only for N2 at 77K.
        r = 2 * gamma * Vm /(RT log(Pr)
        gamma = liquid/vapor surface tension = 8.94 mN/m
        Vm = molar volume of liquid N2 = 34.84 mL/mol
        R = universal gas constant = 8.314 J.K−1.mol−1
        T = 77.3 K

    :param Pr: Relative pressure
    :param F: This is the fraction of pores open at both end (F=0 for desorption).
    :return: The Kelvin radius in A.
    """
    C = -9.62
    return C / ((1+F) * np.log(Pr))



def tFit(Pr):
    """ Return the thickness of adsorbed layer (in A) according to 'Pr'.

        The thickness of adsorbed layer is calculated with 4 different
        equations according to the Pr range in order to be as close a
        possible to experimental data recorded on non porous adsorbents.
    :param Pr: The relative pressure
    :return: The thickness of adsorbed layer (in A)
    """
    t = 0.0
    if Pr < 0.13:
        t = -78.0 * Pr * Pr + 25.0 * Pr + 2.23
    elif Pr >= 0.13 and Pr < 0.55:
        t = 7.23 * Pr + 3.28
    elif Pr >= 0.55 and Pr < 0.7:
        t = 13.15 * Pr * Pr - 7.13 * Pr + 7.24
    elif Pr >= 0.7:
        t = 57.68 * Pr * Pr - 73.19 * Pr + 31.63
    return t

def tHalsey(Pr):
    """ Return the thickness of adsorbed layer (in A) according to 'Pr'.

    :param Pr: The relative pressure
    :return: The thickness of adsorbed layer (in A)
    """
    return 3.54 * (-5.0/np.log(Pr))**0.33333

def tHarkins(Pr):
    """ Return the thickness of adsorbed layer (in A) according to 'Pr'.

    :param Pr: The relative pressure
    :return: The thickness of adsorbed layer (in A)
    """
    return (1.399/(0.034 - np.log10(Pr)))**0.5


def PSDcalc(iso, tcurv='tfit', geom='cylindric'):
    """ Compute the PSD from N2 adsorption isotherm.

        Pore Size Distribution (PSD) is calculated with BJH method.
        The PSD is saved to the file "PSD.txt". This file contains 4 vectors:
        the pore width (Wp), the pore volume (Vp), the pore volume divided
        by the pore width difference (dV/dW) and the cumulative pore volume (Vcum).

    :param iso: Curve (2 vectors) containing the isotherm.
    :param tcurv: String indicating the thickness curve to use. Possible values
                  are "tfit", "halsey" or "harkins".
    :param geom: Pore geometry. Currently only cylindrical pore is implemented.
    :return: A tuple (err, msg) where err = True if an error occurred,
             and msg contains either the error message or information.
    """
    errmsg = None
    err = False
    Pr = iso[0]
    Va = iso[1]
    npt = Pr.size
    if Pr[0] > Pr[npt-1]:
        branch = 'desorption'
        F = 0
    else:
        branch = "adsorption"
        # Reverse data order
        Pr = Pr[::-1]
        Va = Va[::-1]
        F = 1
    imin = 0
    while Pr[imin] > 0.995:
        imin += 1
    imax = npt-1
    while Pr[imax] < 0.3:
        imax -= 1
    Pr = Pr[imin:imax]
    Va = Va[imin:imax]

    npt = Pr.size
    t = np.zeros(npt)
    rp = np.zeros(npt)
    rpm = np.zeros(npt)
    rk = np.zeros(npt)
    Vp = np.zeros(npt)
    Ap = np.zeros(npt)
    SAp = np.zeros(npt)
    SVp = np.zeros(npt)

    for i in range(0, npt):
        rk[i] = KelvinRadius(Pr[i], F)
        if tcurv == 'halsey':
            t[i] = tHalsey(Pr[i])
        elif tcurv == 'harkins':
            t[i] = tHarkins(Pr[i])
        else:
            t[i] = tFit(Pr[i])
        rp[i] = rk[i] + t[i]

    for i in range(1, npt):
        rpm[i] = (rp[i-1] + rp[i]) / 2.0
        dt = t[i-1] - t[i]
        tm = (t[i - 1] + t[i])/2
        dVliq = (Va[i-1] - Va[i]) * gas2liq
        R = (rp[i]/(rk[i]+dt))**2
        Vp[i] = R * (dVliq - dt * SAp[i-1] * 1e-4)
        if Vp[i] < 0.0:
            Vp[i] = 0.0
            Ap[i] = 0.0
            SAp[i] = SAp[i-1]
            SVp[i] = SVp[i-1]
        else:
            Ap[i] = 20000.0 * Vp[i] / rpm[i]
            c = (rpm[i]-tm)/rpm[i]
            SAp[i] = SAp[i-1] + c * Ap[i]
            SVp[i] = SVp[i-1] + Vp[i]

    if branch == 'desorption':
        # Revert the order to have increasing diameters
        rp = np.array(rp[::-1])
        Vp = np.array(Vp[::-1])
        Ap = np.array(Ap[::-1])
        
    # Convert Pore with in nm
    Wp = rp * 0.2
    # Calculation of Dp/dw
    dW = np.diff(Wp)
    Vp = Vp[:-1]
    Vcum = np.cumsum(Vp)
    dVdW = Vp / dW
    Wp = Wp[:-1]

    # Save the Pore Size Distribution in file
    header = "PSD for {} isotherm\n".format(branch)
    header += "Thickness curve = {}\n".format(tcurv)
    header += "plot Wp,dVdW\n"
    header += "plot Wp,Vcum,2\n"
    header += "labX Pore width (nm)\n"
    header += "labY1 dV/dW (mL/g)\n"
    header += "labY2 Cumulative pore volume (mL/g)\n"
    header += "Wp\tVp\tdVdW\tVcum"
    numform = ['%5.1f', '%7.5f', '%7.5f', '%7.4f']
    data = np.stack((Wp, Vp, dVdW, Vcum), axis=-1)
    np.savetxt("PSD.txt", data, delimiter='\t', fmt=numform, header=header)
    return err, errmsg
