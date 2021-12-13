from pandas import DataFrame

import pickle
import pkg_resources

from .metadata import __copyright__, __license__, __version__

class JavaBackend(object):

	def __init__(self):
		pass

	def dumps(self, arguments):
		return pickle.dumps(arguments, protocol = 2)

	def loads(self, results):
		return pickle.loads(results)

	def newObject(self, className, *args):
		raise NotImplementedError()

	def staticInvoke(self, className, methodName, *args):
		raise NotImplementedError()

	def toJavaError(self, e):
		return e

class JavaObject(object):

	def __init__(self, backend):
		self.backend = backend

class JavaError(JavaObject, Exception):

	def __init__(self, backend, className, message, stackTraceElements):
		super(JavaError, self).__init__(backend)
		self.className = className
		self.message = message
		self.stackTraceElements = stackTraceElements

	def __str__(self):
		return "{0}: {1}".format(self.className, self.message)

	def isInstance(self, className):
		clazz = self.backend.staticInvoke("java.lang.Class", "forName", className)
		selfClazz = self.backend.staticInvoke("java.lang.Class", "forName", self.className)
		return clazz.isAssignableFrom(selfClazz)

class ModelField(JavaObject):

	def __init__(self, backend, javaModelField):
		super(ModelField, self).__init__(backend)
		self.javaModelField = javaModelField
		# Transform Java objects to Python strings
		self.name = javaModelField.getName()
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
		try:
			self.javaEvaluator.verify()
		except Exception as e:
			raise self.backend.toJavaError(e)
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
		arguments = self.backend.dumps(arguments)
		try:
			results = self.backend.staticInvoke("org.jpmml.evaluator.python.PythonUtil", "evaluate", self.javaEvaluator, arguments)
		except Exception as e:
			raise self.backend.toJavaError(e)
		results = self.backend.loads(results)
		return results

	def evaluateAll(self, arguments_df):
		argument_records = arguments_df.to_dict(orient = "records")
		argument_records = self.backend.dumps(argument_records)
		try:
			result_records = self.backend.staticInvoke("org.jpmml.evaluator.python.PythonUtil", "evaluateAll", self.javaEvaluator, argument_records)
		except Exception as e:
			raise self.backend.toJavaError(e)
		result_records = self.backend.loads(result_records)
		return DataFrame.from_records(result_records)

class BaseModelEvaluatorBuilder(JavaObject):

	def __init__(self, backend, javaModelEvaluatorBuilder):
		super(BaseModelEvaluatorBuilder, self).__init__(backend)
		self.javaModelEvaluatorBuilder = javaModelEvaluatorBuilder

	def setReportingValueFactoryFactory(self):
		javaValueFactoryFactory = self.backend.staticInvoke("org.jpmml.evaluator.reporting.ReportingValueFactoryFactory", "newInstance")
		self.javaModelEvaluatorBuilder.setValueFactoryFactory(javaValueFactoryFactory)
		return self

	def setCheckSchema(self, checkSchema = True):
		self.javaModelEvaluatorBuilder.setCheckSchema(checkSchema)

	def build(self):
		try:
			javaEvaluator = self.javaModelEvaluatorBuilder.build()
		except Exception as e:
			raise self.backend.toJavaError(e)
		return Evaluator(self.backend, javaEvaluator)

class ModelEvaluatorBuilder(BaseModelEvaluatorBuilder):

	def __init__(self, backend, javaPMML, lax = False):
		javaModelEvaluatorBuilder = backend.newObject("org.jpmml.evaluator.ModelEvaluatorBuilder", javaPMML)
		super(ModelEvaluatorBuilder, self).__init__(backend, javaModelEvaluatorBuilder)
		self.setCheckSchema(not lax)

class LoadingModelEvaluatorBuilder(BaseModelEvaluatorBuilder):

	def __init__(self, backend, lax = False):
		javaModelEvaluatorBuilder = backend.newObject("org.jpmml.evaluator.LoadingModelEvaluatorBuilder")
		super(LoadingModelEvaluatorBuilder, self).__init__(backend, javaModelEvaluatorBuilder)
		self.setCheckSchema(not lax)

	def setLocatable(self, locatable = False):
		self.javaModelEvaluatorBuilder.setLocatable(locatable)
		return self

	def loadFile(self, path):
		file = self.backend.newObject("java.io.File", path)
		self.javaModelEvaluatorBuilder.load(file)
		return self

def make_evaluator(backend, path, lax = False, locatable = False, reporting = False):
	""" Builds an Evaluator based on a PMML file.

	Parameters:
	----------
	backend: JavaBackend
		The Java backend.

	path: string
		The path to the PMML file in local filesystem.

	lax: boolean
		If True, skip model schema sanity checks.

	locatable: boolean
		If True, retain SAX Locator information (if available),
		which leads to more informative exception messages.

	reporting: boolean
		If True, activate the reporting Value API.
	"""
	evaluatorBuilder = LoadingModelEvaluatorBuilder(backend, lax) \
		.setLocatable(locatable) \
		.loadFile(path)
	if reporting:
		evaluatorBuilder.setReportingValueFactoryFactory()
	return evaluatorBuilder.build()

def _package_data_jars(package_data_dir):
	jars = []
	resources = pkg_resources.resource_listdir(package_data_dir, "")
	for resource in resources:
		if resource.endswith(".jar"):
			jars.append(pkg_resources.resource_filename(package_data_dir, resource))
	return jars

def _classpath(user_classpath):
	return _package_classpath() + user_classpath

def _package_classpath():
	return _package_data_jars("jpmml_evaluator.resources") + _package_data_jars("jpmml_evaluator.dependencies")