import sys

from argparse import ArgumentParser

import pandas

from jpmml_evaluator import make_evaluator

def main():
	parser = ArgumentParser(description = "JPMML-Evaluator command-line application")
	parser.add_argument("model", type = str, help = "Model PMML file")
	parser.add_argument("-i", "--input", type = str, help = "Input CSV file")
	parser.add_argument("-o", "--output", type = str, help = "Output CSV file")
	parser.add_argument("--sep", type = str, default = ",", help = "CSV separator character")

	args = parser.parse_args()

	evaluator = make_evaluator(args.model)
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
