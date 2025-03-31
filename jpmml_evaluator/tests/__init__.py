import os

from pathlib import Path
from unittest import TestCase

import numpy
import pandas

from jpmml_evaluator import make_backend, make_evaluator, Evaluator, JavaError, PythonEvaluatorUtil

def _resource(name):
	return os.path.join(os.path.dirname(__file__), "resources", name)

class EvaluatorBuilderTest(TestCase):

	def workflow(self, backend):

		if isinstance(backend, str):
			backend = make_backend(backend)

		resource = _resource("DecisionTreeIris.pmml")

		self.assertIsInstance(resource, str)

		evaluator = make_evaluator(resource, backend = backend)

		self.assertIsInstance(evaluator, Evaluator)

		resource_path = Path(resource)

		self.assertIsInstance(resource_path, Path)

		evaluator = make_evaluator(resource_path, backend = backend)

		self.assertIsInstance(evaluator, Evaluator)

		with open(resource, "rb") as file:
			resource_bytes = bytes(file.read())

		self.assertIsInstance(resource_bytes, bytes)

		evaluator = make_evaluator(resource_bytes, backend = backend)

		self.assertIsInstance(evaluator, Evaluator)

		with open(resource, "r") as file:
			resource_string = file.read()

		self.assertIsInstance(resource_string, str)

		evaluator = make_evaluator(resource_string, backend = backend)

		self.assertIsInstance(evaluator, Evaluator)

class EvaluatorTest(TestCase):

	def workflow(self, backend, lax):

		if isinstance(backend, str):
			backend = make_backend(backend)

		pyArguments = {
			"missing" : None,
			"str" : str("one"),
			"int" : int(1),
			"float" : float(1.0),
			"bool" : bool(True)
		}
		pyResults = PythonEvaluatorUtil.evaluate(backend, None, pyArguments, None)

		self.assertDictEqual(pyArguments, pyResults)

		numpyArguments = {
			"int8" : numpy.int8(1),
			"int16" : numpy.int16(1),
			"int32" : numpy.int32(1),
			"float32" : numpy.float32(1.0),
			"float64" : numpy.float64(1.0)
		}
		numpyResults = PythonEvaluatorUtil.evaluate(backend, None, numpyArguments, None)

		self.assertDictEqual({"int8" : 1, "int16" : 1, "int32" : 1, "float32" : float(1.0), "float64" : float(1.0)}, numpyResults)

		evaluator = make_evaluator(_resource("DecisionTreeIris.pmml"), backend = backend, lax = lax, reporting = True, transpile = True) \
			.verify()

		self.assertEqual(2, len(evaluator.getInputFields()))
		self.assertEqual(1, len(evaluator.getTargetFields()))
		self.assertEqual(4, len(evaluator.getOutputFields()))

		targetField = evaluator.getTargetFields()[0]

		probabilityOutputFields = evaluator.getOutputFields()[0:3]
		reportOutputField = evaluator.getOutputFields()[-1]

		self.assertEqual("Species", targetField.getName())
		self.assertEqual("string", targetField.getDataType())
		self.assertEqual("categorical", targetField.getOpType())

		arguments = {
			"Sepal.Length" : "error",
			"Sepal.Width" : "error",
			"Petal.Length" : "error",
			"Petal.Width" : "error"
		}
		print(arguments)

		try:
			results = evaluator.evaluate(arguments)

			self.fail()
		except JavaError as je:
			self.assertIsNotNone(je.className)
			self.assertIsNotNone(je.message)
			self.assertTrue(len(je.stackTraceElements) > 0)
			self.assertFalse(je.isInstance("java.lang.String"))
			self.assertTrue(je.isInstance("org.jpmml.evaluator.ValueCheckException"))
			self.assertTrue(je.isInstance("org.jpmml.evaluator.EvaluationException"))
			self.assertFalse(je.isInstance("org.jpmml.model.InvalidMarkupException"))
			self.assertFalse(je.isInstance("org.jpmml.model.UnsupportedMarkupException"))
			self.assertTrue(je.isInstance("org.jpmml.model.PMMLException"))
			self.assertTrue(je.isInstance("java.lang.RuntimeException"))

		arguments = {
			"Sepal.Length" : 5.1,
			"Sepal.Width" : 3.5,
			"Petal.Length" : 1.4,
			"Petal.Width" : 0.2
		}
		print(arguments)

		results = evaluator.evaluate(arguments)
		print(results)

		self.assertEqual(5, len(results))

		self.assertEqual("setosa", results["Species"])
		self.assertEqual(1.0, results["probability(setosa)"])
		self.assertEqual(0.0, results["probability(versicolor)"])
		self.assertEqual(0.0, results["probability(virginica)"])
		self.assertTrue(results["report(probability(versicolor))"].startswith("<math "))

		evaluator.suppressResultFields([targetField])
		self.assertTrue(hasattr(evaluator, "dropColumns"))

		results = evaluator.evaluate(arguments)

		self.assertEqual(4, len(results))

		evaluator.suppressResultFields([])
		self.assertFalse(hasattr(evaluator, "dropColumns"))

		arguments_df = pandas.read_csv(_resource("Iris.csv"), sep = ",")
		print(arguments_df.head(5))

		results_df = evaluator.evaluateAll(arguments_df, parallelism = 1)
		#print(results_df.head(5))

		self.assertEqual((150, 5), results_df.shape)
		self.assertEqual(arguments_df.index.tolist(), results_df.index.tolist())
		self.assertIsNot(arguments_df.index, results_df.index)

		arguments_df.set_index(("row_{}".format(row + 1) for row in arguments_df.index.tolist()), inplace = True) 

		evaluator.suppressResultFields([reportOutputField])

		results_df, errors = evaluator.evaluateAll(arguments_df, error_col = None, parallelism = 3)

		self.assertEqual((150, 4), results_df.shape)
		self.assertEqual(arguments_df.index.tolist(), results_df.index.tolist())
		self.assertEqual(["row_1", "row_2", "row_3"], results_df.index.tolist()[0:3])
		self.assertIsNot(arguments_df.index, results_df.index)

		expected_results_df = pandas.read_csv(_resource("DecisionTreeIris.csv"), sep = ",")

		self.assertEqual(expected_results_df.columns.tolist(), results_df.columns.tolist())

		targetFieldName = targetField.getName()
		self.assertEqual(expected_results_df[targetFieldName].values.tolist(), results_df[targetFieldName].values.tolist())

		probabilityOutputFieldNames = [probabilityOutputField.getName() for probabilityOutputField in probabilityOutputFields]
		self.assertTrue(numpy.allclose(expected_results_df[probabilityOutputFieldNames], results_df[probabilityOutputFieldNames], rtol = 1e-13, atol = 1e-13))

		self.assertIsNone(errors)

		arguments_df.iloc[13, :] = "error"

		results_df = evaluator.evaluateAll(arguments_df)

		self.assertEqual((150, 5), results_df.shape)
		self.assertEqual(arguments_df.index.tolist(), results_df.index.tolist())

		self.assertEqual(1, results_df["errors"].count())
		self.assertEqual(None, results_df["Species"][13])
		self.assertEqual("org.jpmml.evaluator.ValueCheckException: Field \"Petal.Length\" cannot accept invalid value \"error\"", results_df["errors"][13])

		results_df, errors = evaluator.evaluateAll(arguments_df, error_col = None)

		self.assertEqual((150, 4), results_df.shape)
		self.assertEqual(arguments_df.index.tolist(), results_df.index.tolist())

		self.assertEqual(None, results_df["Species"][13])

		self.assertEqual((150,), errors.shape)
		self.assertEqual(arguments_df.index.tolist(), errors.index.tolist())

		self.assertEqual(1, errors.count())
		self.assertEqual("org.jpmml.evaluator.ValueCheckException: Field \"Petal.Length\" cannot accept invalid value \"error\"", errors[13])

		evaluator.suppressResultFields(None)
