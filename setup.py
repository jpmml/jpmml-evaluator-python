from distutils.core import setup

exec(open("jpmml_evaluator/metadata.py").read())

setup(
	name = "jpmml_evaluator",
	version = __version__,
	description = "PMML evaluator library for Python",
	author = "Villu Ruusmann",
	author_email = "villu.ruusmann@gmail.com",
	url = "https://github.com/jpmml/jpmml-evaluator-python",
	download_url = "https://github.com/jpmml/jpmml-evaluator-python/archive/" + __version__ + ".tar.gz",
	license = __license__,
	packages = [
		"jpmml_evaluator",
		"jpmml_evaluator.dependencies",
		"jpmml_evaluator.resources",
	],
	package_data = {
		"jpmml_evaluator.dependencies" : ["*.jar"],
		"jpmml_evaluator.resources" : ["*.jar"]
	},
	install_requires = [
		"jpype1",
		"pandas",
		"py4j",
		"pyjnius>=1.2.1"
	]
)
