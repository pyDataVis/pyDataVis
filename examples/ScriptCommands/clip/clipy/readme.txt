Test for "clipy" script command

Open the file "clipy.plt"

Enter the following lines in script window and execute them (Ctrl+E)
Yclip = Y
clipup Yclip 1
clipdn Yclip -1
plot X,Y
plot X,Yclip

You should obtain a chart like the image in clipy.png.

