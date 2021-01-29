all: deps build

deps:
	pip3 install -r requirements.txt
build: clean
	nuitka3 --follow-imports --onefile --standalone --assume-yes-for-downloads --verbose qbitools.py
	mv qbitools.bin qbitools
install:
	cp ./qbitools /usr/local/bin/qbitools
clean:
	rm -rf ./dist ./build ./qbitools.build ./qbitools.dist
