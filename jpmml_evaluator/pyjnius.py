from jpmml_evaluator import _classpath, JavaError, JNIBackend

class PyJNIusBackend(JNIBackend):

	def __init__(self):
		super(PyJNIusBackend, self).__init__()

	@classmethod
	def createJVM(cls, user_classpath = []):
		import jnius_config

		jnius_config.set_classpath(*_classpath(user_classpath = user_classpath))

	@classmethod
	def destroyJVM(cls):
		pass

	def loads(self, results):
		# Unpack jnius.ByteArray to byte array
		results = bytearray(results[:])
		return super(PyJNIusBackend, self).loads(results)

	def _loadJavaClass(self, className):
		from jnius import autoclass
		return autoclass(className)

	def newObject(self, className, *args):
		javaClass = self._ensureJavaClass(className)
		return javaClass(*args)

	def staticInvoke(self, className, methodName, *args):
		if className == "java.lang.Class" and methodName == "forName":
			from jnius import find_javaclass
			return find_javaclass(*args)
		javaClass = self._ensureJavaClass(className)
		javaMember = javaClass.__dict__[methodName]
		return javaMember(*args)

	def toJavaError(self, e):
		from jnius import JavaException
		if isinstance(e, JavaException):
			return JavaError(self, e.classname, e.innermessage, e.stacktrace)
		return e
