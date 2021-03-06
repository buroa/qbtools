all: clean deps build package

deps:
	pip3 install -r requirements.txt
	curl -L https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage -o appimagetool
	chmod +x appimagetool
	sed -i 's|AI\x02|\x00\x00\x00|' appimagetool
	./appimagetool --appimage-extract
	rm appimagetool
	mv squashfs-root appimagetool
package:
	cp ./resources/* qbittools.dist/
	./appimagetool/AppRun qbittools.dist/ --comp xz -n qbittools
build: clean
	nuitka3 --follow-imports --standalone --assume-yes-for-downloads qbittools.py
install:
	cp ./qbittools /usr/local/bin/qbittools
clean:
	rm -rf ./dist ./build ./qbittools.build ./qbittools.dist ./appimagetool
