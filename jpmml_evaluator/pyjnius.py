import jnius_config

from jpmml_evaluator import _classpath, JavaBackend, JavaError

def jnius_configure_classpath(user_classpath = []):
	jnius_config.set_classpath(*_classpath(user_classpath = user_classpath))

class PyJNIusBackend(JavaBackend):

	def __init__(self):
		super(PyJNIusBackend, self).__init__()

	def loads(self, results):
		# Unpack jnius.ByteArray to byte array
		results = bytearray(results[:])
		return super(PyJNIusBackend, self).loads(results)

	def newObject(self, className, *args):
		from jnius import autoclass
		javaClass = autoclass(className)
		return javaClass(*args)

	def staticInvoke(self, className, methodName, *args):
		if className == "java.lang.Class" and methodName == "forName":
			from jnius import find_javaclass
			return find_javaclass(*args)
		from jnius import autoclass
		javaClass = autoclass(className)
		javaMember = javaClass.__dict__[methodName]
		return javaMember(*args)

	def toJavaError(self, e):
		from jnius import JavaException
		if isinstance(e, JavaException):
			return JavaError(self, e.classname, e.innermessage, e.stacktrace)
		return e
