from setuptools import find_packages, setup

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
	packages = find_packages(exclude = ["*.tests.*", "*.tests"]),
	package_data = {
		"jpmml_evaluator.dependencies" : ["*.jar"],
		"jpmml_evaluator.resources" : ["*.jar"]
	},
	exclude_package_data = {
		"" : ["README.md"],
	},
	entry_points={
		"console_scripts" : [
			"jpmml_evaluator=jpmml_evaluator.cli:main",
		],
	},
	python_requires = ">=3.8",
	install_requires = [
		"jpype1",
		"pandas",
		"py4j",
		"pyjnius>=1.2.1"
	]
)
