#!/usr/bin/env python

from pandas import DataFrame
from py4j.java_collections import JavaMap
from py4j.java_gateway import JavaGateway

import jnius_config
import os
import pkg_resources

from .metadata import __copyright__, __license__, __version__

class JavaBackend(object):

	def __init__(self):
		pass

	def newObject(self, className, *args):
		raise ValueError()

	def staticInvoke(self, className, methodName, *args):
		raise ValueError()

def jnius_configure_classpath(user_classpath = []):
	jnius_config.set_classpath(*_classpath(user_classpath))

class PyJNIusBackend(JavaBackend):

	def __init__(self):
		super(PyJNIusBackend, self).__init__()

	def newObject(self, className, *args):
		from jnius import autoclass
		javaClass = autoclass(className)
		return javaClass(*args)

	def staticInvoke(self, className, methodName, *args):
		from jnius import autoclass
		javaClass = autoclass(className)
		javaMember = javaClass.__dict__[methodName]
		return javaMember(*args)

def launch_gateway(user_classpath = []):
	return JavaGateway.launch_gateway(classpath = os.pathsep.join(_classpath(user_classpath)))

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

class JavaObject(object):

	def __init__(self, backend):
		self.backend = backend

class ModelField(JavaObject):

	def __init__(self, backend, javaModelField):
		super(ModelField, self).__init__(backend)
		self.javaModelField = javaModelField
		# Transform Java objects to Python strings
		self.name = javaModelField.getName().getValue()
		self.dataType = javaModelField.getDataType().value()
		self.opType = javaModelField.getOpType().value()

	def __str__(self):
		return self.javaModelField.toString()

	def getName(self):
		return self.name

	def getDataType(self):
		return self.dataType

	def getOpType(self):
		return self.opType

def _initModelFields(backend, javaModelFields):
	return [ModelField(backend, javaModelFields.get(i)) for i in range(javaModelFields.size())]

class Evaluator(JavaObject):

	def __init__(self, backend, javaEvaluator):
		super(Evaluator, self).__init__(backend)
		self.javaEvaluator = javaEvaluator

	def verify(self):
		self.javaEvaluator.verify()
		return self

	def getInputFields(self):
		if not hasattr(self, "inputFields"):
			self.inputFields = _initModelFields(self.backend, self.javaEvaluator.getInputFields())
		return self.inputFields

	def getTargetFields(self):
		if not hasattr(self, "targetFields"):
			self.targetFields = _initModelFields(self.backend, self.javaEvaluator.getTargetFields())
		return self.targetFields

	def getOutputFields(self):
		if not hasattr(self, "outputFields"):
			self.outputFields = _initModelFields(self.backend, self.javaEvaluator.getOutputFields())
		return self.outputFields

	def evaluate(self, arguments):
		javaArguments = self.backend.newObject("java.util.LinkedHashMap")
		for k, v in arguments.items():
			javaFieldName = self.backend.staticInvoke("org.dmg.pmml.FieldName", "create", k)
			if isinstance(v, str):
				javaObject = self.backend.newObject("java.lang.String", v)
			elif isinstance(v, int):
				javaObject = self.backend.newObject("java.lang.Integer", v)
			elif isinstance(v, float):
				javaObject = self.backend.newObject("java.lang.Double", v)
			elif isinstance(v, bool):
				javaObject = self.backend.newObject("java.lang.Boolean", v)
			else:
				raise ValueError()
			javaArguments.put(javaFieldName, javaObject)
		javaResults = self.javaEvaluator.evaluate(javaArguments)
		results = self.backend.staticInvoke("org.jpmml.evaluator.EvaluatorUtil", "decode", javaResults)
		pyResults = {entry.getKey() : entry.getValue() for entry in results.entrySet().toArray()}
		return pyResults

	def evaluateAll(self, arguments_df):
		argument_records = arguments_df.to_dict(orient = "records")
		result_records = []
		for argument_record in argument_records:
			result_record = self.evaluate(argument_record)
			result_records.append(result_record)
		return DataFrame.from_records(result_records)

class BaseModelEvaluatorBuilder(JavaObject):

	def __init__(self, backend, javaModelEvaluatorBuilder):
		super(BaseModelEvaluatorBuilder, self).__init__(backend)
		self.javaModelEvaluatorBuilder = javaModelEvaluatorBuilder

	def build(self):
		javaEvaluator = self.javaModelEvaluatorBuilder.build()
		return Evaluator(self.backend, javaEvaluator)

class ModelEvaluatorBuilder(BaseModelEvaluatorBuilder):

	def __init__(self, backend, javaPMML):
		javaModelEvaluatorBuilder = backend.newObject("org.jpmml.evaluator.ModelEvaluatorBuilder", javaPMML)
		super(ModelEvaluatorBuilder, self).__init__(backend, javaModelEvaluatorBuilder)

class LoadingModelEvaluatorBuilder(BaseModelEvaluatorBuilder):

	def __init__(self, backend):
		javaModelEvaluatorBuilder = backend.newObject("org.jpmml.evaluator.LoadingModelEvaluatorBuilder")
		super(LoadingModelEvaluatorBuilder, self).__init__(backend, javaModelEvaluatorBuilder)

	def setLocatable(self, locatable = False):
		self.javaModelEvaluatorBuilder.setLocatable(locatable)
		return self

	def setDefaultVisitorBattery(self):
		visitors = self.backend.newObject("org.jpmml.evaluator.DefaultVisitorBattery")
		self.javaModelEvaluatorBuilder.setVisitors(visitors)
		return self

	def loadFile(self, path):
		file = self.backend.newObject("java.io.File", path)
		self.javaModelEvaluatorBuilder.load(file)
		return self

def _classpath(user_classpath):
	return _package_classpath() + user_classpath

def _package_classpath():
	jars = []
	resources = pkg_resources.resource_listdir("jpmml_evaluator.resources", "")
	for resource in resources:
		if resource.endswith(".jar"):
			jars.append(pkg_resources.resource_filename("jpmml_evaluator.resources", resource))
	return jars
