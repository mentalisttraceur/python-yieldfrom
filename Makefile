default:
	python setup.py sdist
	python setup.py bdist_wheel --python-tag py20
	rm build/lib/yieldfrom.py
	python setup.py bdist_wheel --python-tag py26.py3

clean:
	rm -rf __pycache__ build *.egg-info dist
	rm -f *.py[oc] MANIFEST yieldfrom.py

test:
	cp normal.py yieldfrom.py
	pytest test.py
	python3 test.py
	python2 test.py
	cp no_except_as.py yieldfrom.py
	python2 test.py
