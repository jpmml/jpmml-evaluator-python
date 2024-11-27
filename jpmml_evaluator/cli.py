import sys

from argparse import ArgumentParser

import pandas

from jpmml_evaluator import make_evaluator

def main():
	parser = ArgumentParser(prog = "jpmml_evaluator", description = "JPMML-Evaluator command-line application")
	parser.add_argument("model", type = str, help = "Model PMML file")
	parser.add_argument("--backend", type = str, default = "jpype", help = "Java backend. One of 'jpype', 'pyjnius' or 'py4j'")
	parser.add_argument("--transpile", action = "store_true", help = "Transpile PMML to Java")
	parser.add_argument("-i", "--input", type = str, help = "Input CSV file. If absent, read from system input")
	parser.add_argument("-o", "--output", type = str, help = "Output CSV file. If absent, write to system output")
	parser.add_argument("--sep", type = str, default = ",", help = "CSV separator character")

	args = parser.parse_args()

	evaluator = make_evaluator(args.model, backend = args.backend, transpile = args.transpile)
	evaluator.verify()

	if args.input:
		input = args.input
	else:
		input = sys.stdin

	if args.output:
		output = args.output
	else:
		output = sys.stdout

	arguments = pandas.read_csv(input, sep = args.sep)	
	results = evaluator.evaluateAll(arguments)
	results.to_csv(output, sep = args.sep, header = True, index = False)
