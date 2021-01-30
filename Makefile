all: deps build package

deps:
	pip3 install -r requirements.txt
	curl -L https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage -o appimagetool
	chmod +x appimagetool
	sed -i 's|AI\x02|\x00\x00\x00|' appimagetool
	./appimagetool --appimage-extract
	rm appimagetool
	mv squashfs-root appimagetool
package:
	cp ./resources/* qbitools.dist/
	./appimagetool/AppRun qbitools.dist/ --comp xz -n qbitools
build: clean
	nuitka3 --follow-imports --standalone --assume-yes-for-downloads --verbose qbitools.py
install:
	cp ./qbitools /usr/local/bin/qbitools
clean:
	rm -rf ./dist ./build ./qbitools.build ./qbitools.dist
