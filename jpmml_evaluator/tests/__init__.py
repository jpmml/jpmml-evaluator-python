import os

from unittest import TestCase

import numpy
import pandas

from jpmml_evaluator import make_backend, make_evaluator, JavaError

def _resource(name):
	return os.path.join(os.path.dirname(__file__), "resources", name)

def _argumentsToResults(backend, arguments):
	arguments = backend.dumps(arguments)
	results = backend.staticInvoke("org.jpmml.evaluator.python.PythonUtil", "argumentsToResults", arguments)
	results = backend.loads(results)
	return results

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
		pyResults = _argumentsToResults(backend, pyArguments)

		self.assertDictEqual(pyArguments, pyResults)

		numpyArguments = {
			"int8" : numpy.int8(1),
			"int16" : numpy.int16(1),
			"int32" : numpy.int32(1),
			"float32" : numpy.float32(1.0),
			"float64" : numpy.float64(1.0)
		}
		numpyResults = _argumentsToResults(backend, numpyArguments)

		self.assertDictEqual({"int8" : 1, "int16" : 1, "int32" : 1, "float32" : float(1.0), "float64" : float(1.0)}, numpyResults)

		evaluator = make_evaluator(_resource("DecisionTreeIris.pmml"), backend = backend, lax = lax, reporting = True) \
			.verify()

		self.assertEqual(2, len(evaluator.getInputFields()))
		self.assertEqual(1, len(evaluator.getTargetFields()))
		self.assertEqual(4, len(evaluator.getOutputFields()))

		targetField = evaluator.getTargetFields()[0]

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

		results_df = evaluator.evaluateAll(arguments_df)
		print(results_df.head(5))

		self.assertEqual((150, 5), results_df.shape)

		evaluator.suppressResultFields([targetField])

		results_df = evaluator.evaluateAll(arguments_df)

		self.assertEqual((150, 4), results_df.shape)

		evaluator.suppressResultFields(None)