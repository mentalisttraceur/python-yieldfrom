default:
	python setup.py sdist bdist_wheel --universal

clean:
	rm -rf __pycache__ *.py[oc] build *.egg-info dist MANIFEST

test:
	pytest test.py
	python3 test.py
	python2 test.py
