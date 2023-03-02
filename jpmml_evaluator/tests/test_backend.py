# Both JPype and PyJNIus tests would like to create a new JVM instance.
# Unfortunately, a Python process can only be associated with one JVM instance, 
# so it will be necessary to disable one of the two backends.
from .jpype import JPypeEvaluatorTest
from .py4j import Py4JEvaluatorTest
#from .pyjnius import PyJNIusEvaluatorTest