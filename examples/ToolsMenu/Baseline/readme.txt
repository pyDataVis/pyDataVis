Test for "Baseline" option in "Tools' menu.

It is the user which defines the baseline position by clicking on the curve. The baseline curve can be build from these points by two methods according to the type:
	* Linear, the curve is build by concatenation of the line segments
	  connecting the points.
	* Cubic spine, the curve is build by cubic spine interpolation 
	  between the points.
Once a method is chosen, it is not possible to change it.

Open the file "baseline.plt".

Select the "Baseline" option in "Tools' menu.

Keep the default method, "Cubic Spine" and click on an area outside the peaks. Left click adds a new point at the mouse position, right click deletes the point which was already around.
The first left click, only a red star is added on the curve. For the second left click a straight line is drawn and it is only after the fourth click that the spine curve is drawn. Actually this because you need fourth points to calculate a cubic spline. 

If you click on Correct button the baseline is subtracted from the original data.
If you click on "Add BL" button a new vector containing the baseline is added to the data block.




