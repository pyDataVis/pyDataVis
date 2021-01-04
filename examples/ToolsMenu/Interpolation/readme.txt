Test for "Interpolation" option in "Tools' menu.

Open the file "interpol.plt".

Select the "Interpolation" option in "Tools' menu.

This open the interactive interpolation tool. There are 4 parameters:
	* the data block (here we have no choice as there is only one block).
	* dx, which is the distance between points on abscissa. 
	  We see that this value = 1 because it is the current value.
	* s, which is the smoothing parameter. Larger s means more smoothing.
	  Here we have s = 0 which means that the curve will pass through
	  all data points.
	* k, which is the degree of the spline fit (1 <= k <= 5). 
	  It is recommended to use cubic splines (k=3).
	  Even values of k should be avoided.

Set dx to 0.25. This add 3 extra values between each data points (see interpol.png).

When you click on "OK" the original data is replaced by the blue curve, the window is closed and the Plotting area is updated.



