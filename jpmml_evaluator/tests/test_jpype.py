from jpmml_evaluator.jpype import JPypeBackend

from . import EvaluatorTest

class JPypeEvaluatorTest(EvaluatorTest):

	def setUp(self):
		JPypeBackend.createJVM()

	def tearDown(self):
		JPypeBackend.destroyJVM()

	def test_jpype(self):
		backend = JPypeBackend()
		super(JPypeEvaluatorTest, self).workflow(backend, lax = False)
