from jpmml_evaluator.pyjnius import PyJNIusBackend

from . import EvaluatorTest

class PyJNIusEvaluatorTest(EvaluatorTest):

	def setUp(self):
		PyJNIusBackend.createJVM()

	def tearDown(self):
		PyJNIusBackend.destroyJVM()

	def test_pyjnius(self):
		super(PyJNIusEvaluatorTest, self).workflow("pyjnius", lax = True)
