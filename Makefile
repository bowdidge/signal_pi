all: test

test:
	python2 -m unittest discover -p "*_test.py"
	python3 -m unittest discover -p "*_test.py"

clean:
	rm *.pyc
