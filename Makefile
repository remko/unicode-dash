DOCSET_NAME=UnicodeCharacters
DOCSET_DIR=$(DOCSET_NAME).docset
DOCSET_PACKAGE=$(DOCSET_NAME).tgz
DASH_DIR=dash

all: build

build: ucd.nounihan.flat.xml
	python3 generate.py

dist: clean build
	tar --exclude='.DS_Store' -czf $(DOCSET_PACKAGE) $(DOCSET_DIR)
	cp docset.json $(DOCSET_PACKAGE) $(DASH_DIR)/docsets/$(DOCSET_NAME)

clean:
	-rm -rf \
		$(DOCSET_DIR)/Contents/Resources/Documents/c \
		$(DOCSET_DIR)/Contents/Resources/docSet.dsidx \
		$(DOCSET_PACKAGE) \
		docset.json

ucd.nounihan.flat.xml: 
	curl -O https://www.unicode.org/Public/UCD/latest/ucdxml/ucd.nounihan.flat.zip
	unzip ucd.nounihan.flat.zip
	rm ucd.nounihan.flat.zip

