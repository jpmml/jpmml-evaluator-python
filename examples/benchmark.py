from jpmml_evaluator import make_evaluator
from timeit import Timer

import pandas
import statistics
import sys

evaluate_stmt = """
rows = df.to_dict(orient = "records")
for row in rows:
	evaluator.evaluate(row)
"""

evaluateAll_stmt = """
evaluator.evaluateAll(df, parallelism = 1)
"""

def benchmark(evaluator, df):
	def _run(stmt):
		print(stmt)
		timings = Timer(stmt = stmt, globals = globals()).repeat(number = 100)
		min_time = min(timings)
		max_time = max(timings)
		mean_time = statistics.mean(timings)
		median_time = statistics.median(timings)
		print("range: [{}, {}]".format(min_time, max_time))
		print("mean: {}".format(mean_time))
		print("median: {}".format(median_time))

	_run(evaluate_stmt)

	_run(evaluateAll_stmt)
	_run(evaluateAll_stmt.replace("parallelism = 1", "parallelism = -1"))

if __name__ == "__main__":
	pmml_file = sys.argv[1]
	csv_file = sys.argv[2]
	backend = sys.argv[3] if len(sys.argv) > 3 else "jpype"

	evaluator = make_evaluator(pmml_file, backend = backend) \
		.verify()
	print(evaluator)

	df = pandas.read_csv(csv_file)
	print(df)

	benchmark(evaluator, df)