from jpmml_evaluator.py4j import Py4JBackend

from . import EvaluatorTest

class Py4JEvaluatorTest(EvaluatorTest):

	def setUp(self):
		Py4JBackend.createGateway()

	def tearDown(self):
		Py4JBackend.destroyGateway()

	def test_py4j(self):
		backend = Py4JBackend()
		super(Py4JEvaluatorTest, self).workflow(backend, lax = False)
