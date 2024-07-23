import pickle

from abc import abstractmethod, abstractclassmethod, ABC
from pandas import DataFrame

import numpy
import pkg_resources

from .metadata import __copyright__, __license__, __version__

def _canonicalize(arguments, nan_as_missing):
	if nan_as_missing:
		for key, value in arguments.items():
			arguments[key] = (None if (isinstance(value, (float, numpy.single, numpy.double)) and numpy.isnan(value)) else value)
	return arguments

def _canonicalizeAll(arguments_df, nan_as_missing):
	if nan_as_missing:
		arguments_df = arguments_df.replace({numpy.nan: None})
	return arguments_df

class JavaBackend(ABC):

	def __init__(self):
		self.javaClasses_ = {}

	def dumps(self, arguments):
		return pickle.dumps(arguments, protocol = 2)

	def loads(self, results):
		return pickle.loads(results)

	def _ensureJavaClass(self, className):
		try:
			return self.javaClasses_[className]
		except KeyError:
			javaClass = self._loadJavaClass(className)
			self.javaClasses_[className] = javaClass
			return javaClass

	@abstractmethod
	def _loadJavaClass(self, className):
		raise NotImplementedError()

	@abstractmethod
	def newObject(self, className, *args):
		raise NotImplementedError()

	@abstractmethod
	def staticInvoke(self, className, methodName, *args):
		raise NotImplementedError()

	@abstractmethod
	def toJavaError(self, e):
		return e

class JNIBackend(JavaBackend):

	def __init__(self):
		super(JNIBackend, self).__init__()

	@abstractclassmethod
	def ensureJVM(cls):
		raise NotImplementedError()

	@abstractclassmethod
	def createJVM(cls, user_classpath = []):
		raise NotImplementedError()

	@abstractclassmethod
	def destroyJVM(cls):
		raise NotImplementedError()

class JavaObject(object):

	def __init__(self, backend):
		if not isinstance(backend, JavaBackend):
			raise TypeError()
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

	def evaluate(self, arguments, nan_as_missing = True):
		arguments = _canonicalize(arguments, nan_as_missing = nan_as_missing)
		arguments = self.backend.dumps(arguments)
		try:
			results = self.backend.staticInvoke("org.jpmml.evaluator.python.PythonUtil", "evaluate", self.javaEvaluator, arguments)
		except Exception as e:
			raise self.backend.toJavaError(e)
		results = self.backend.loads(results)
		if hasattr(self, "dropColumns"):
			for dropColumn in self.dropColumns:
				del results[dropColumn]
		return results

	def evaluateAll(self, arguments_df, nan_as_missing = True):
		arguments_df = _canonicalizeAll(arguments_df, nan_as_missing = nan_as_missing)
		arguments_dict = {
			"columns" : arguments_df.columns.tolist(),
			"data" : arguments_df.values.tolist()
		}
		arguments = self.backend.dumps(arguments_dict)
		try:
			results = self.backend.staticInvoke("org.jpmml.evaluator.python.PythonUtil", "evaluateAll", self.javaEvaluator, arguments)
		except Exception as e:
			raise self.backend.toJavaError(e)
		results_dict = self.backend.loads(results)
		results_df = DataFrame(data = results_dict["data"], index = (arguments_df.index.copy() if (len(arguments_dict["data"]) == len(results_dict["data"])) else None), columns = results_dict["columns"])
		if hasattr(self, "dropColumns"):
			for dropColumn in self.dropColumns:
				results_df.drop(str(dropColumn), axis = 1, inplace = True)
		return results_df

	def predict(self, X):
		return self.evaluateAll(X)

	def suppressResultFields(self, resultFields):
		if resultFields:
			self.dropColumns = [resultField.getName() for resultField in resultFields]
		else:
			if hasattr(self, "dropColumns"):
				del self.dropColumns

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

	def transform(self, javaPMMLTransformer):
		self.javaModelEvaluatorBuilder.transform(javaPMMLTransformer)
		return self

	def transpile(self, path = None):
		if path:
			file = self.backend.newObject("java.io.File", path)
			transpiler = self.backend.newObject("org.jpmml.transpiler.FileTranspiler", None, file)
		else:
			transpiler = self.backend.newObject("org.jpmml.transpiler.InMemoryTranspiler", None)
		transformer = self.backend.newObject("org.jpmml.transpiler.TranspilerTransformer", transpiler)
		return self.transform(transformer)

def make_backend(alias):
	if not isinstance(alias, str):
		raise TypeError()
	if alias.lower() == "jpype":
		from jpmml_evaluator.jpype import JPypeBackend
		return JPypeBackend()
	elif alias.lower() == "pyjnius":
		from jpmml_evaluator.pyjnius import PyJNIusBackend
		return PyJNIusBackend()
	elif alias.lower() == "py4j":
		from jpmml_evaluator.py4j import Py4JBackend
		return Py4JBackend()
	else:
		aliases = ["jpype", "pyjnius", "py4j"]
		raise ValueError("Java backend alias {0} not in {1}".format(alias, aliases))

def make_evaluator(path, backend = "jpype", lax = False, locatable = False, reporting = False, transpile = False):
	""" Builds an Evaluator based on a PMML file.

	Parameters:
	----------
	path: string
		The path to the PMML file in local filesystem.

	backend: JavaBackend or string
		The Java backend or its alias

	lax: boolean
		If True, skip model schema sanity checks.

	locatable: boolean
		If True, retain SAX Locator information (if available),
		which leads to more informative exception messages.

	reporting: boolean
		If True, activate the reporting Value API.

	transpile: boolean or string
		If not False, perform transpilation.
	"""

	if isinstance(backend, JavaBackend):
		pass
	elif isinstance(backend, str):
		backend = make_backend(backend)
	else:
		raise TypeError()

	evaluatorBuilder = LoadingModelEvaluatorBuilder(backend, lax) \
		.setLocatable(locatable) \
		.loadFile(path)
	if reporting:
		evaluatorBuilder.setReportingValueFactoryFactory()
	if transpile:
		evaluatorBuilder.transpile(transpile if isinstance(transpile, str) else None)
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
