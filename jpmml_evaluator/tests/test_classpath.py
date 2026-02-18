from unittest import TestCase

from jpmml_evaluator import _classpath

class ClasspathTest(TestCase):

	def test_classpath(self):
		classpath = _classpath([])
		self.assertEqual(1 + 25, len(classpath))
