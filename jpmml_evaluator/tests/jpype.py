from . import EvaluatorTest
from jpmml_evaluator.jpype import start_jvm, shutdown_jvm, JPypeBackend

class JPypeEvaluatorTest(EvaluatorTest):

	def setUp(self):
		start_jvm()

	def tearDown(self):
		shutdown_jvm()

	def test_jpype(self):
		backend = JPypeBackend()
		super(JPypeEvaluatorTest, self).workflow(backend, lax = False)