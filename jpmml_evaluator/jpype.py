import importlib

import jpype
import jpype.imports

from jpmml_evaluator import _classpath, JavaBackend, JavaError

def start_jvm(user_classpath = []):
	jpype.startJVM(classpath = _classpath(user_classpath = user_classpath))

def shutdown_jvm():
	jpype.shutdownJVM()

class JPypeBackend(JavaBackend):

	def __init__(self):
		super(JPypeBackend, self).__init__()
		self.javaClasses_ = {}

	def _ensure_class(self, className):
		try:
			return self.javaClasses_[className]
		except KeyError:
			javaClass = importlib.import_module(className)
			self.javaClasses_[className] = javaClass
			return javaClass

	def newObject(self, className, *args):
		javaClass = self._ensure_class(className)
		return javaClass(*args)

	def staticInvoke(self, className, methodName, *args):
		javaClass = self._ensure_class(className)
		javaMember = getattr(javaClass, methodName)
		return javaMember(*args)

	def toJavaError(self, e):
		from jpype import JException
		if isinstance(e, JException):
			return JavaError(self, e.getClass().getName(), e.getMessage(), e.getStackTrace())
		return e
