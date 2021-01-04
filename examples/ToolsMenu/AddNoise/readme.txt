Test for "Add Noise" option in "Tools' menu.

Open the file "AddNoise.plt".

Select the "Add Noise" option in "Tools' menu. This open the Add Noise tool.

You can tune the noise addition with two parameters:
- Location, which is the mean (centre) of the distribution. It defaults to 0.0, that is the noise is uniformly distributed on both sides of the curve.
- Scale, which is the standard deviation (spread or “width”) of the distribution. Must be non-negative. The initial value given by pyDataVis is 1/100 of data span.

Change these parameters and click on "Compute" to see the result.

When you click on "OK" the original data is replaced by the blue curve, the window is closed and the Plotting area is updated.






