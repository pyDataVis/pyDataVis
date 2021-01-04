Test for "Execute a Python script" option in the Script menu.

Open the file pyscript.plt

Enter the following lines in the Script window and execute (Ctrl+E):

import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

def func(x, a, b):
    return a * np.log(-b * np.log(x))
popt, pcov = curve_fit(func, X, Y)

sresult = "Best fit parameters: a={0:g}, b={1:g}".format(popt[0], popt[1])
print (sresult)
plt.plot(X, Y, 'bo')
plt.plot(X, func(X, *popt), 'r-')
plt.suptitle(sresult)
plt.show()
