Test for "Peak Find" option in "Tools' menu.

Open the file "peakFind.plt".

Select the "Peak Find" option in "Tools' menu.

A small dialog pops up where you can input the peak detection parameters, which are the minimum peak height and minimum peak width. Based on an analysis of the data, pyDataVis proposes 1 for height and 40 for width. If we accept these parameters by clicking OK, an information window tells us that 7 peaks have ben detected. We see that number is too high. We need to increase the detection parameter values. Giving them the values 4 and 60 limits the peak number to 2. If we accept this value by clicking yes, this calls the Peak Fitting module.

We see that the fitting is not good. This is because the fitting was done with the default peak shape which is the Gaussian model. This is not suitable because these peaks are asymmetric.

It is possible to change the peak model by replacing the peak parameters, G, by another type in the Peak parameters area at the bottom of the window. If, for both peaks, we replace G by AG (Asymmetric Gaussian) and click Compute the fitting is faily improved.

The best fit for two peaks is obtained with the AP (Asymmetric Pseudo-Voigt) peak type as shown on the picture peakFind.png.

Clicking on OK generates the file “peakFit.txt” and opens a new pyDataVis window to display its content. As shown on peakFit.png image, there are four curves: the experimental data, the sum of peaks and the curve for each peak.



