.PHONY: build clean package
.DEFAULT: build

clean:
	rm -rf build/
	mkdir -p build/packages
	mkdir -p build/sublime
	mkdir -p build/yaml

build: clean
	pipenv install
	pipenv run python3 main.py

package:
	cp extras/* build/sublime/
	zip -jr build/packages/AdvancedAnsibleSnippets.sublime-package build/sublime/*.sublime-snippet

deploy:
	cp build/packages/AdvancedAnsibleSnippets.sublime-package ~/.config/sublime-text/Installed\ Packages/AdvancedAnsibleSnippets.sublime-package

all: build package deploy