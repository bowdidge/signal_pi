all: test

test:
	python -m unittest discover -p "*_test.py"

clean:
	rm *.pyc
