Test for "Peak Find" option in "Tools' menu.

Open the file "peakFind.plt".

Select the "Peak Find" option in "Tools' menu.

A small dialog pops up where you can input the peak detection parameters, which are the minimum peak height and minimum peak width. Based on an analysis of the data, pyDataVis proposes 600 for height and 2 for width. If we accept these parameters by clicking OK, an information window tells us that only 4 peaks have ben detected. To detect all the peaks we need to change the detection parameter values. Giving them the values 300 and 0.1 allows to detect the 8 peaks. If we accept this value by clicking yes, this calls the Peak Fitting module.

We see that the fitting could be improved. This is because it was done with the default peak shape which is the Gaussian model. It is possible to change the peak model by replacing the peak parameters, G, by another type in the Peak parameters area at the bottom of the window. If, for all peaks, we replace G by L (Lorentzian) and click Compute the fitting is somewhat improved.

Clicking on OK generates the file “peakFit.txt” and opens a new pyDataVis window to display its content. As shown on peakFit.png image, there are 10 curves: the experimental data, the sum of peaks and the curve for each peak.



