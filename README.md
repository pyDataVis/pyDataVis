# pyDataVis

**pyDataVis** is an open source application for interactive visualization, analysis and manipulation of scientific data. There are many [free plotting software](https://en.wikipedia.org/wiki/Category:Free_plotting_software) most of them far more powerful than *pyDataVis*. However, in terms of simplicity, it is hard to beat. Indeed it is designed to be very easy to use, just drag and drop your data file in *pyDataVis* window and immediately you are seeing the curves. For now, *pyDataVis* is limited to 2D plotting.

*pyDataVis* is written in [Python](https://en.wikipedia.org/wiki/Python_(programming_language)) and use [PyQt](https://riverbankcomputing.com/software/pyqt/) as graphic user interface (GUI) and [Matplotlib](https://matplotlib.org/) for plotting.


## Installation

### Installation from Debian package
This package can be found on the [website](https://pyDataVis.github.io) of pyDataVis, in [Downloads page](https://pydatavis.github.io/Downloads.html).
Assuming that the .deb file is in Downloads folder, to install, open a Terminal and type:
```
cd Downloads
sudo dpkg -i pyDataVis.deb
```

### Installation from Windows package
This package archive can be found on the [website](https://pyDataVis.github.io) of pyDataVis, in [Downloads page](https://pydatavis.github.io/Downloads.html).
To install, copy the .zip file to the location where you want store the program. Then extract all files from the archive. To launch the application, in the folder pyDataVis, execute the file *pyDataVis.exe*.

To remove the application you only have to delete the pyDataVis folder.

### Installation from source archives
pyDataVis requires Python 3, PyQt5, Numpy, Pandas, Scipy and Matplotlib. The easiest way to install everything is to use Open Source [Anaconda](https://www.anaconda.com/products/individual) that will "just work" out of the box for Windows, macOS and common Linux platforms.

The source archives can be found on the [website](https://pyDataVis.github.io) of pyDataVis, in [Downloads page](https://pydatavis.github.io/Downloads.html). Extract the archive to the place where you want to store the program.

You can instead clone the repository if you have [git](https://git-scm.com/) installed.
Open a Terminal and change the current working directory to the location where you want to clone pyDataVis, for example ~/myprog:
```
cd ~/myprog
```
Then type:
```
git clone https://github.com/pyDataVis/pyDataVis.git
```

To launch the application, change the current working directory to the pyDataVis folder, for example ~/myprog/pyDataVis:
```
cd ~/myprog/pyDataVis
```
and execute the pyDataVis.py script:
```
python pyDataVis.py
```


# Support
To display the manual, open the page https://pydatavis.github.io/ in your browser or use the *Help* option in the *Help* menu.

The folder *examples*, in the source archives, contains files for testing almost any function. For those who have not installed from source archives, they can be found on the [website](https://pyDataVis.github.io) of pyDataVis, in [Downloads page](https://pydatavis.github.io/Downloads.html).

If you need more information, feel free to contact me at: palphonse@wanadoo.fr


## License
[MIT](https://choosealicense.com/licenses/mit/)


## Author
Pierre Alphonse
palphonse@wanadoo.fr


## Contributing
This is a one-man project made by a non-professional. There must be many thing to improve.
Any help is welcome.


## Roadmap
This version is the first release. 
It was developed on Linux, briefly tested on Windows 10 but not yet tested on Mac OS X.


