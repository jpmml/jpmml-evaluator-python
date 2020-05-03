from pandas import DataFrame

import pkg_resources

from .metadata import __copyright__, __license__, __version__

class JavaBackend(object):

	def __init__(self):
		pass

	def newObject(self, className, *args):
		raise NotImplementedError()

	def dict2map(self, pyDict):
		raise NotImplementedError()

	def map2dict(self, javaMap):
		raise NotImplementedError()

	def staticInvoke(self, className, methodName, *args):
		raise NotImplementedError()

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
		javaArguments = self.backend.dict2map(arguments)
		javaArguments = self.backend.staticInvoke("org.jpmml.evaluator.EvaluatorUtil", "encodeKeys", javaArguments)
		javaResults = self.javaEvaluator.evaluate(javaArguments)
		javaResults = self.backend.staticInvoke("org.jpmml.evaluator.EvaluatorUtil", "decodeAll", javaResults)
		results = self.backend.map2dict(javaResults)
		return results

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

	def setReportingValueFactoryFactory(self):
		javaValueFactoryFactory = self.backend.staticInvoke("org.jpmml.evaluator.reporting.ReportingValueFactoryFactory", "newInstance")
		self.javaModelEvaluatorBuilder.setValueFactoryFactory(javaValueFactoryFactory)
		return self

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

	def loadFile(self, path):
		file = self.backend.newObject("java.io.File", path)
		self.javaModelEvaluatorBuilder.load(file)
		return self

def make_evaluator(backend, path, locatable = False, reporting = False):
	""" Builds an Evaluator based on a PMML file.

	Parameters:
	----------
	backend: JavaBackend
		The Java backend.

	path: string
		The path to the PMML file in local filesystem.

	locatable: boolean
		If True, retain SAX Locator information (if available),
		which leads to more informative exception messages.

	reporting: boolean
		If True, activate the reporting Value API.
	"""
	evaluatorBuilder = LoadingModelEvaluatorBuilder(backend) \
		.setLocatable(locatable) \
		.loadFile(path)
	if reporting:
		evaluatorBuilder.setReportingValueFactoryFactory()
	return evaluatorBuilder.build()

def _classpath(user_classpath):
	return _package_classpath() + user_classpath

def _package_classpath():
	jars = []
	resources = pkg_resources.resource_listdir("jpmml_evaluator.resources", "")
	for resource in resources:
		if resource.endswith(".jar"):
			jars.append(pkg_resources.resource_filename("jpmml_evaluator.resources", resource))
	return jars
