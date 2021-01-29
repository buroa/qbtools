all: deps build

deps:
	pip3 install -r requirements.txt

build: clean
	pyinstaller qbitools.py --onefile \
		--hidden-import commands.add --hidden-import commands.export --hidden-import commands.reannounce \
		--hidden-import commands.update_passkey --hidden-import commands.tagging
install:
	cp ./dist/qbitools /usr/local/bin/qbitools
clean:
	rm -rf ./dist ./build
