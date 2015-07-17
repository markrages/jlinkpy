install:
	python setup.py install

build:
	python setup.py build

MANIFEST:
	python setup.py sdist --manifest-only

clean:
	rm -f *.pyc *~ jlink/*.pyc jlink/*~
	rm -f MANIFEST
	rm -rf build
