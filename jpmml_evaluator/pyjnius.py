from jpmml_evaluator import _classpath, JavaBackend

import jnius_config

def jnius_configure_classpath(user_classpath = []):
	jnius_config.set_classpath(*_classpath(user_classpath))

class PyJNIusBackend(JavaBackend):

	def __init__(self):
		super(PyJNIusBackend, self).__init__()

	def newObject(self, className, *args):
		from jnius import autoclass
		javaClass = autoclass(className)
		return javaClass(*args)

	def dict2map(self, pyDict):
		javaMap = self.newObject("java.util.LinkedHashMap")
		for k, v in pyDict.items():
			javaKey = self.newObject("java.lang.String", k)
			if isinstance(v, str):
				javaValue = self.newObject("java.lang.String", v)
			elif isinstance(v, int):
				javaValue = self.newObject("java.lang.Integer", v)
			elif isinstance(v, float):
				javaValue = self.newObject("java.lang.Double", v)
			elif isinstance(v, bool):
				javaValue = self.newObject("java.lang.Boolean", v)
			else:
				raise ValueError()
			javaMap.put(javaKey, javaValue)
		return javaMap

	def map2dict(self, javaMap):
		entries = javaMap.entrySet().toArray()
		pyDict = {entry.getKey() : entry.getValue() for entry in entries}
		return pyDict

	def staticInvoke(self, className, methodName, *args):
		from jnius import autoclass
		javaClass = autoclass(className)
		javaMember = javaClass.__dict__[methodName]
		return javaMember(*args)
