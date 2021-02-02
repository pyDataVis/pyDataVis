Test of the option "CIF" in the Convert menu.

- Open the CIF file "Si-COD-9008566.cif" for silicon taken from the COD database.
- Then select in the Convert menu, the "CIF" option. 
- The simulated XRD pattern is computed from the CIF file and saved in a new file having the same name as the CIF file but with .plt extension ("Si-COD-9008566.plt"). This file is loaded in a new pyDataVis window which shows the simulated pattern.
- Close the window containing the CIF file.
- Open the experimental XRD pattern of silicon which is in the file "Si-Std.txt".
- Go to the "Si-COD-9008566.plt" window and copy the simulated pattern (Curve > Copy).
- Return to "Si-Std.txt" window and paste the curve.
- The experimental pattern stop at 80°, thus delete the range above 80° with the script command:
"clipx > 80".
- You should get something like the picture in "SiXRD.png". This confirms that the experimental pattern fits well with the simulated one.



