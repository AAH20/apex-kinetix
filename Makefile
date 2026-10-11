.PHONY: test benchmark master clean

test:
	PYTHONPATH=. python3 -m unittest discover -s tests -v

benchmark:
	PYTHONPATH=. python3 benchmarks_runner.py

master:
	PYTHONPATH=. python3 benchmarks/run_master_test.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
