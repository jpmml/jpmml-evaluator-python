from jpmml_evaluator import make_evaluator
from jpmml_evaluator.pyjnius import jnius_configure_classpath, PyJNIusBackend
from jpmml_evaluator.py4j import launch_gateway, Py4JBackend
from unittest import TestCase

import os
import pandas

jnius_configure_classpath()

def _resource(name):
	return os.path.join(os.path.dirname(__file__), "resources", name)

class EvaluatorTest(TestCase):

	def workflow(self, backend):
		pyDict = {
			"str" : str("one"),
			"int" : int(1),
			"float" : float(1.0),
			"bool" : bool(True)
		}

		javaMap = backend.dict2map(pyDict)
		pyJavaDict = backend.map2dict(javaMap)

		self.assertDictEqual(pyDict, pyJavaDict)

		evaluator = make_evaluator(backend, _resource("DecisionTreeIris.pmml"), reporting = True) \
			.verify()

		self.assertEqual(2, len(evaluator.getInputFields()))
		self.assertEqual(1, len(evaluator.getTargetFields()))
		self.assertEqual(4, len(evaluator.getOutputFields()))

		targetField = evaluator.getTargetFields()[0]

		self.assertEqual("Species", targetField.getName())
		self.assertEqual("string", targetField.getDataType())
		self.assertEqual("categorical", targetField.getOpType())

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

		arguments_df = pandas.read_csv(_resource("Iris.csv"), sep = ",")
		print(arguments_df.head(5))

		results_df = evaluator.evaluateAll(arguments_df)
		print(results_df.head(5))

		self.assertEqual((150, 5), results_df.shape)

class PyJNIusEvaluatorTest(EvaluatorTest):

	def test_pyjnius(self):
		backend = PyJNIusBackend()
		super(PyJNIusEvaluatorTest, self).workflow(backend)

class Py4JEvaluatorTest(EvaluatorTest):

	def setUp(self):
		self.gateway = launch_gateway()

	def tearDown(self):
		self.gateway.shutdown()

	def test_py4j(self):
		backend = Py4JBackend(self.gateway)
		super(Py4JEvaluatorTest, self).workflow(backend)
