import sys  
sys.path.append("../")  

import numpy as np

from utils import isNumber, isNumeric, isNotNumeric, isNumData, commaToDot
from utils import round_to_n, arrayToString


def test_isNumber():
   assert isNumber(0.1) == True
   assert isNumber('0.1') == True
   assert isNumber('1e3') == True


def test_isNumeric():
   assert isNumeric([]) == False
   assert isNumeric([0, '1', 2]) == True
   assert isNumeric([0, '.1', 2]) == True


def test_isNotNumeric():
   assert isNotNumeric([]) == True
   assert isNotNumeric(['a', '1', 2]) == True
   assert isNotNumeric([0, '.1.', 2]) == True


def test_isNumData():
   assert isNumData("") == False
   assert isNumData(10) == True
   assert isNumData("1,2,3") == True
   assert isNumData("1,2;3 4") == False


def test_commaToDot():
   assert commaToDot("1,23;2,45:0,1") == "1.23;2.45:0.1"


def test_round_to_n():
   assert round_to_n(0.045624, 3) == 0.0456
   assert round_to_n(0.45624, 3) == 0.456
   assert round_to_n(1.45624, 2) == 1.5
   assert round_to_n(14.5624, 4) == 14.56


def test_arrayToString():
   X = np.linspace(1., 4., 4)
   Y = X * X
   A = np.vstack((X, Y))
   txt = arrayToString(A)
   assert txt == "1.0\t1.0\n2.0\t4.0\n3.0\t9.0\n4.0\t16.0\n"



   












 





