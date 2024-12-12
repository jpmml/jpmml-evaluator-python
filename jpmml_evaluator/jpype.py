import importlib

import jpype
import jpype.imports

from jpmml_evaluator import _classpath, JavaError, JNIBackend

class JPypeBackend(JNIBackend):

	def __init__(self):
		super(JPypeBackend, self).__init__()
		JPypeBackend.ensureJVM()

	@classmethod
	def ensureJVM(cls):
		if not jpype.isJVMStarted():
			cls.createJVM()
		importlib.import_module("org.jpmml.evaluator.python.PythonUtil")

	@classmethod
	def createJVM(cls, user_classpath = []):
		jpype.startJVM(classpath = _classpath(user_classpath = user_classpath))

	@classmethod
	def destroyJVM(cls):
		jpype.shutdownJVM()

	def _loadJavaClass(self, className):
		return importlib.import_module(className)

	def newObject(self, className, *args):
		javaClass = self._ensureJavaClass(className)
		return javaClass(*args)

	def newArray(self, className, values):
		return list(values)

	def staticInvoke(self, className, methodName, *args):
		javaClass = self._ensureJavaClass(className)
		javaMember = getattr(javaClass, methodName)
		return javaMember(*args)

	def toJavaError(self, e):
		from jpype import JException
		if isinstance(e, JException):
			return JavaError(self, e.getClass().getName(), e.getMessage(), e.getStackTrace())
		return e
