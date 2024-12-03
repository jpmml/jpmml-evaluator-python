from unittest import TestCase

from jpmml_evaluator.pyjnius import PyJNIusBackend

from . import EvaluatorTest, EvaluatorBuilderTest

class PyJNIusEvaluatorTest(TestCase):

	def setUp(self):
		PyJNIusBackend.createJVM()

	def tearDown(self):
		PyJNIusBackend.destroyJVM()

	def test_evaluatorBuilder(self):
		EvaluatorBuilderTest().workflow("pyjnius")

	def test_evaluator(self):
		EvaluatorTest().workflow("pyjnius", lax = True)
