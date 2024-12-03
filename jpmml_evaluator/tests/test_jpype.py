from unittest import TestCase

from jpmml_evaluator.jpype import JPypeBackend

from . import EvaluatorTest, EvaluatorBuilderTest

class JPypeEvaluatorTest(TestCase):

	def setUp(self):
		JPypeBackend.createJVM()

	def tearDown(self):
		JPypeBackend.destroyJVM()

	def test_evaluatorBuilder(self):
		EvaluatorBuilderTest().workflow("jpype")

	def test_evaluator(self):
		EvaluatorTest().workflow("jpype", lax = False)
