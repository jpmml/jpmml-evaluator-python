from jpmml_evaluator.py4j import launch_gateway, Py4JBackend

from . import EvaluatorTest

class Py4JEvaluatorTest(EvaluatorTest):

	def setUp(self):
		self.gateway = launch_gateway()

	def tearDown(self):
		self.gateway.shutdown()

	def test_py4j(self):
		backend = Py4JBackend(self.gateway)
		super(Py4JEvaluatorTest, self).workflow(backend, lax = False)
