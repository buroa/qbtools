.PHONY: build

all: clean deps build package

deps:
	pip3 install -U -r requirements.txt
build:
	pyoxidizer build --release
	strip ./build/x86_64-unknown-linux-gnu/release/install/qbittools
	upx --best --lzma ./build/x86_64-unknown-linux-gnu/release/install/qbittools
install:
	cp ./build/x86_64-unknown-linux-gnu/release/install/qbittools /usr/local/bin/qbittools
clean:
	rm -rf ./dist ./build
