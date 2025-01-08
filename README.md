JPMML-Evaluator-Python [![Build Status](https://github.com/jpmml/jpmml-evaluator-python/workflows/pytest/badge.svg)](https://github.com/jpmml/jpmml-evaluator-python/actions?query=workflow%3A%22pytest%22)
======================

PMML evaluator library for Python.

# Features #

This package provides Python wrapper classes and functions for the [JPMML-Evaluator](https://github.com/jpmml/jpmml-evaluator) library.

# Prerequisites #

* Java Platform, Standard Edition 8 or newer.
* Python 3.8 or newer.

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

## Command-line application ##

The `jpmml_evaluator` module is executable.
The main application loads the model from the PMML file, and scores all data records from the input CSV file or stream; scoring results are written to the output CSV file or stream:

```
python -m jpmml_evaluator DecisionTreeIris.pmml --input Iris.csv --output DecisionTreeIris.csv
```

If the input CSV file (`-i` or `--input`) and/or the output CSV file (`-o` or `--output`) is not specified, then system input (`sys.stdin`) and system output (`sys.stdout`), respectively, are assumed:

```
python -m jpmml_evaluator DecisionTreeIris.pmml < Iris.csv > DecisionTreeIris.csv
```

Getting help:

```
python -m jpmml_evaluator --help
```

On some platforms, the [Pip](https://pypi.org/project/pip/) package installer additionally makes the main application available as a top-level command:

```
jpmml_evaluator DecisionTreeIris.pmml < Iris.csv > DecisionTreeIris.csv
```

## Library ##

### Java-to-Python API mapping ###

Guiding principles:

1. Java package prefix `org.jpmml.evaluator` becomes Python package prefix `jpmml_evaluator`.
2. Java classes and interfaces become Python classes with the same name.
3. Java methods become Python methods with the same name. In case of method overloading, the names of Python methods may have a disambiguating suffix (eg. `loadFile`, `loadInputStream`) appended to them.
4. Java parameter types become Python parameter types.

For example, the Java method `org.jpmml.evaluator.Evaluator#evaluate(Map<FieldName, ?> arguments)` has become a Python method `jpmml_evaluator.Evaluator.evaluate(arguments: dict)`.

### Java backend ###

The communication with the JPMML-Evaluator library is managed by a `jpmml_evaluator.JavaBackend` object.

Currently, it's possible to choose between three backend implementations:

| &nbsp; | JPype | PyJNIus | Py4J |
|--------|-------|---------|------|
| GitHub project page | [jpype-project/jpype](https://github.com/jpype-project/jpype) | [kivy/pyjnius](https://github.com/kivy/pyjnius) | [bartdag/py4j](https://github.com/bartdag/py4j) |
| Python package | `jpype1` | `pyjnius` | `py4j` |
| Implementation class | `jpmml_evaluator \` `.jpype.JPypeBackend` | `jpmml_evaluator \` `.pyjnius.PyJNIusBackend` | `jpmml_evaluator \` `.py4j.Py4JBackend` |
| Implementation class alias | `"jpype"` | `"pyjnius"` | `"py4j"` |
| Type | Local JVM via JNI | Local JVM via JNI | Local or remote JVM via TCP/IP sockets |
| Restartable | No | No | Yes |
| Timing* for `evaluate(X)` | 8.1 -- 9.4 | 10.8 -- 11.9 | 37.3 -- 40.2 |
| Timing* for `evaluateAll(X)` | 2.55 -- 2.95 | 2.77 -- 3.18 | 3.27 -- 3.62 |

[*] - Relative timings (smaller is better).

### Workflow ###

Building a verified model evaluator from a PMML file:

```python
from jpmml_evaluator import make_evaluator

evaluator = make_evaluator("DecisionTreeIris.pmml") \
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
from jpmml_evaluator import JavaError

arguments = {
	"Sepal_Length" : 5.1,
	"Sepal_Width" : 3.5,
	"Petal_Length" : 1.4,
	"Petal_Width" : 0.2
}

try:
	results = evaluator.evaluate(arguments)
	print(results)
except JavaError as je:
	pass
```

Evaluating a collection of data records:

```python
import pandas

arguments_df = pandas.read_csv("Iris.csv", sep = ",")

results_df = evaluator.evaluateAll(arguments_df, error_col = "errors")
print(results_df)

# The error column is added to the results DataFrame only if there was something erroneous happening
errors = df_results["errors"] if "errors" in results_df.columns else None
if errors is not None:
	pass
```

Alternatively, getting the results DataFrame and errors Series as separate objects:

```python
results_df, errors = evaluator.evaluateAll(arguments_df, error_col = None)
print(results_df)

if errors is not None:
	pass
```

# License #

JPMML-Evaluator-Python is licensed under the terms and conditions of the [GNU Affero General Public License, Version 3.0](https://www.gnu.org/licenses/agpl-3.0.html).
For a quick summary of your rights ("Can") and obligations ("Cannot" and "Must") under AGPLv3, please refer to [TLDRLegal](https://tldrlegal.com/license/gnu-affero-general-public-license-v3-(agpl-3.0)).

If you would like to use JPMML-Evaluator-Python in a proprietary software project, then it is possible to enter into a licensing agreement which makes it available under the terms and conditions of the [BSD 3-Clause License](https://opensource.org/licenses/BSD-3-Clause) instead.

# Additional information #

JPMML-Evaluator-Python is developed and maintained by Openscoring Ltd, Estonia.

Interested in using JPMML software in your software? Please contact [info@openscoring.io](mailto:info@openscoring.io)
