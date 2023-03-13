from jpmml_evaluator.pyjnius import PyJNIusBackend

from . import EvaluatorTest

class PyJNIusEvaluatorTest(EvaluatorTest):

	def setUp(self):
		PyJNIusBackend.createJVM()

	def tearDown(self):
		PyJNIusBackend.destroyJVM()

	def test_pyjnius(self):
		backend = PyJNIusBackend()
		super(PyJNIusEvaluatorTest, self).workflow(backend, lax = True)
