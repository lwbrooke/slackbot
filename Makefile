.PHONY: clean install

build:
	python3 setup.py bdist_wheel

clean:
	rm -rf build/ dist/ fangorn.egg.info/

install: build
	python3 -m pip install --no-binary falcon dist/fangorn*

reinstall: build
	python3 -m pip install --upgrade --no-deps --force-reinstall dist/fangorn*
