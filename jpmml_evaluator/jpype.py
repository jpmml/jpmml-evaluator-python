import importlib

import jpype
import jpype.imports

from jpmml_evaluator import _classpath, JavaError, JNIBackend

class JPypeBackend(JNIBackend):

	def __init__(self):
		super(JPypeBackend, self).__init__()
		self.javaClasses_ = {}

	@classmethod
	def createJVM(cls, user_classpath = []):
		jpype.startJVM(classpath = _classpath(user_classpath = user_classpath))

	@classmethod
	def destroyJVM(cls):
		jpype.shutdownJVM()

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
