.PHONY: clean install

build:
	python3 setup.py bdist_wheel

clean:
	rm -rf build/ dist/ fanghorn.egg.info/

install: build
	python3 -m pip install --no-binary falcon dist/fanghorn*

reinstall: build
	python3 -m pip install --upgrade --no-deps --force-reinstall dist/fanghorn*
