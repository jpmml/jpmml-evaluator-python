from __future__ import absolute_import

import os

from py4j.java_gateway import JavaGateway
from py4j.protocol import Py4JJavaError

from jpmml_evaluator import _classpath, JavaBackend, JavaError

def launch_gateway(user_classpath = []):
	return JavaGateway.launch_gateway(classpath = os.pathsep.join(_classpath(user_classpath = user_classpath)))

class Py4JBackend(JavaBackend):

	def __init__(self, gateway):
		super(Py4JBackend, self).__init__()
		self.gateway = gateway

	def newObject(self, className, *args):
		javaClass = self.gateway.jvm.__getattr__(className)
		return javaClass(*args)

	def staticInvoke(self, className, methodName, *args):
		javaClass = self.gateway.jvm.__getattr__(className)
		javaMember = javaClass.__getattr__(methodName)
		return javaMember(*args)

	def toJavaError(self, e):
		if isinstance(e, Py4JJavaError):
			java_exception = e.java_exception
			return JavaError(self, java_exception.getClass().getName(), java_exception.getMessage(), java_exception.getStackTrace())
		return e
