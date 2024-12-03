from unittest import TestCase

from jpmml_evaluator.py4j import Py4JBackend

from . import EvaluatorTest, EvaluatorBuilderTest

class Py4JEvaluatorTest(TestCase):

	def setUp(self):
		Py4JBackend.createGateway()

	def tearDown(self):
		Py4JBackend.destroyGateway()

	def test_evaluatorBuilder(self):
		EvaluatorBuilderTest().workflow("py4j")

	def test_evaluator(self):
		EvaluatorTest().workflow("py4j", lax = False)
