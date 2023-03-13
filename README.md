JPMML-Evaluator-Python [![Build Status](https://github.com/jpmml/jpmml-evaluator-python/workflows/python/badge.svg)](https://github.com/jpmml/jpmml-evaluator-python/actions?query=workflow%3A%22python%22)
======================

PMML evaluator library for Python.

# Features #

This package provides Python wrapper classes and functions for the [JPMML-Evaluator](https://github.com/jpmml/jpmml-evaluator) library.

# Prerequisites #

* Java Platform, Standard Edition 8 or newer.
* Python 2.7, 3.4 or newer.

# Installation #

Installing a release version from PyPI:

```
pip install jpmml_evaluator
```

Alternatively, installing the latest snapshot version from GitHub:

```
pip install --upgrade git+https://github.com/jpmml/jpmml-evaluator-python.git
```

# Usage #

### Java-to-Python API mapping ###

Guiding principles:

1. Java package prefix `org.jpmml.evaluator` becomes Python package prefix `jpmml_evaluator`.
2. Java classes and interfaces become Python classes with the same name.
3. Java methods become Python methods with the same name. In case of method overloading, the names of Python methods may have a disambiguating suffix (eg. `loadFile`, `loadInputStream`) appended to them.
4. Java parameter types become Python parameter types.

For example, the Java method `org.jpmml.evaluator.Evaluator#evaluate(Map<FieldName, ?> arguments)` has become a Python method `jpmml_evaluator.Evaluator.evaluate(arguments: dict)`.

### Java backend ###

The communication with the JPMML-Evaluator library is managed by a `jpmml_evaluator.JavaBackend` object.

Currently, it's possible to choose between three backends implementations:

| &nbsp; | JPype | PyJNIus | Py4J |
|--------|-------|---------|------|
| GitHub project page | [jpype-project/jpype](https://github.com/jpype-project/jpype) | [kivy/pyjnius](https://github.com/kivy/pyjnius) | [bartdag/py4j](https://github.com/bartdag/py4j) |
| Python package | `jpype1` | `pyjnius` | `py4j` |
| Implementation class | `jpmml_evaluator \` `.jpype.JPypeBackend` | `jpmml_evaluator \` `.pyjnius.PyJNIusBackend` | `jpmml_evaluator \` `.py4j.Py4JBackend` |
| Type | Local JVM via JNI | Local JVM via JNI | Local or remote JVM via TCP/IP sockets |
| Restartable | No | No | Yes |

### Workflow ###

Building a verified model evaluator from a PMML file:

```python
from jpmml_evaluator import make_evaluator
from jpmml_evaluator.jpype import JPypeBackend

evaluator = make_evaluator(JPypeBackend(), "DecisionTreeIris.pmml") \
	.verify()
```

Printing model schema:

```python
inputFields = evaluator.getInputFields()
print("Input fields: " + str([inputField.getName() for inputField in inputFields]))

targetFields = evaluator.getTargetFields()
print("Target field(s): " + str([targetField.getName() for targetField in targetFields]))

outputFields = evaluator.getOutputFields()
print("Output fields: " + str([outputField.getName() for outputField in outputFields]))
```

Evaluating a single data record:

```python
arguments = {
	"Sepal_Length" : 5.1,
	"Sepal_Width" : 3.5,
	"Petal_Length" : 1.4,
	"Petal_Width" : 0.2
}

results = evaluator.evaluate(arguments)
print(results)
```

Evaluating a collection of data records:

```python
import pandas

arguments_df = pandas.read_csv("Iris.csv", sep = ",")

results_df = evaluator.evaluateAll(arguments_df)
print(results_df)
```

# License #

JPMML-Evaluator-Python is licensed under the terms and conditions of the [GNU Affero General Public License, Version 3.0](https://www.gnu.org/licenses/agpl-3.0.html).
For a quick summary of your rights ("Can") and obligations ("Cannot" and "Must") under AGPLv3, please refer to [TLDRLegal](https://tldrlegal.com/license/gnu-affero-general-public-license-v3-(agpl-3.0)).

If you would like to use JPMML-Evaluator-Python in a proprietary software project, then it is possible to enter into a licensing agreement which makes it available under the terms and conditions of the [BSD 3-Clause License](https://opensource.org/licenses/BSD-3-Clause) instead.

# Additional information #

JPMML-Evaluator-Python is developed and maintained by Openscoring Ltd, Estonia.

Interested in using JPMML software in your software? Please contact [info@openscoring.io](mailto:info@openscoring.io)
