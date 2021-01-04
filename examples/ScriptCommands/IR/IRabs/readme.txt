Test of "IRabs" script command.

Open the file "IRabs.txt"

The intensities are in transmittance

To convert them in absorbance, type "IRabs" in the Script window and execute (Ctrl+E).

An information window pop up with the message "Absorbance data out of range".
This is because some points have a value lower than 0.

Click OK and you should get the spectrum in absorbance (like in IRabs.png).

You can avoid the previous message by using the script command "clipdn A 0" before doing the conversion.

