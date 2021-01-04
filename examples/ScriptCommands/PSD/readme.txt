Test for "PSD" script command.

Two data block are required and it is assumed that the adsorption isotherm is contained in the first data block and the desorption isotherm in a second data block. Moreover, in these blocks, the first vector must contain the relative pressure and the second vector the adsorbed volume expressed in mL/g.

The PSD command takes two parameters. The first, which can be either A or D, indicates which isotherm (A-dsorption or D-esorption) is used. The second parameter specifies the equation used for calculating the thickness of adsorbed layer according to the relative pressure (t-curve). This parameter can have one of the three values: halsey, harkins or tfit. These equations are given in the file thicknessCurves.pdf.

To test the PSD command, open the file "PSD-iso.plt".

Type "PSD D halsey"in the Script window and execute (Ctrl+E).

The computation was done with the desorption isotherm and halsey curve. At the end of the process a new file is generated named "PSD-PSD.plt" which contains four vectors: the pore width (Wp), the pore volume (Vp), the pore volume divided by the pore width difference (dV/dW) and the cumulative pore volume (Vcum). This file is loaded in a new pyDataVis window and two curves are plotted, the pore size distribution dV/dW and the cumulative pore volume (see the image PSD.pnd)







