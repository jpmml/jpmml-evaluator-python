from jpmml_evaluator import _canonicalize, _canonicalizeAll
from pandas import DataFrame
from unittest import TestCase

import numpy

class DataTest(TestCase):

	def test_canonicalize(self):
		arguments = {
			"A" : int(1),
			"B" : numpy.NaN,
			"C" : str("3")
		}
		arguments = _canonicalize(arguments, nan_as_missing = True)
		self.assertEqual(3, len(arguments))
		self.assertEqual(int(1), arguments["A"])
		self.assertEqual(None, arguments["B"])
		self.assertEqual(str("3"), arguments["C"])

	def test_canonicalizeAll(self):
		arguments_df = DataFrame([[int(1)], [numpy.NaN], [str("3")]], columns = ["X"])
		self.assertEqual(object, arguments_df["X"].dtype)
		arguments_df = _canonicalizeAll(arguments_df, nan_as_missing = True)
		self.assertEqual((3, 1), arguments_df.shape)
		self.assertEqual(object, arguments_df["X"].dtype)
		self.assertEqual([int(1), None, str("3")], arguments_df["X"].tolist())
