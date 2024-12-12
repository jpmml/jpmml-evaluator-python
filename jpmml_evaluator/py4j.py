from __future__ import absolute_import

import os

from py4j.java_gateway import JavaGateway
from py4j.protocol import Py4JJavaError

from jpmml_evaluator import _classpath, JavaBackend, JavaError

class Py4JBackend(JavaBackend):

	gateway = None


	def __init__(self, gateway = None):
		super(Py4JBackend, self).__init__()
		if not gateway:
			gateway = Py4JBackend.ensureGateway()
		self.gateway = gateway

	@classmethod
	def ensureGateway(cls):
		if not cls.gateway:
			cls.createGateway()
		getattr(cls.gateway.jvm, "org.jpmml.evaluator.python.PythonUtil")
		return cls.gateway

	@classmethod
	def createGateway(cls, user_classpath = []):
		cls.gateway = JavaGateway.launch_gateway(classpath = os.pathsep.join(_classpath(user_classpath = user_classpath)))

	@classmethod
	def destroyGateway(cls):
		cls.gateway.shutdown()
		cls.gateway = None

	def _loadJavaClass(self, className):
		return getattr(self.gateway.jvm, className)

	def newObject(self, className, *args):
		javaClass = self._ensureJavaClass(className)
		return javaClass(*args)

	def newArray(self, className, values):
		javaClass = self._ensureJavaClass(className)
		javaArray = self.gateway.new_array(javaClass, len(values))
		for idx, value in enumerate(values):
			javaArray[idx] = value
		return javaArray

	def staticInvoke(self, className, methodName, *args):
		javaClass = self._ensureJavaClass(className)
		javaMember = getattr(javaClass, methodName)
		return javaMember(*args)

	def toJavaError(self, e):
		if isinstance(e, Py4JJavaError):
			java_exception = e.java_exception
			return JavaError(self, java_exception.getClass().getName(), java_exception.getMessage(), java_exception.getStackTrace())
		return e
