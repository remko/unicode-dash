DOCSET_NAME=UnicodeCharacters
DOCSET_DIR=$(DOCSET_NAME).docset
DOCSET_PACKAGE=$(DOCSET_NAME).tgz
DASH_DIR=dash

all: build

build: ucd.nounihan.flat.xml cldr-annotations.json
	python3 generate.py

dist: clean $(DOCSET_PACKAGE)
	cp docset.json $(DOCSET_PACKAGE) $(DASH_DIR)/docsets/$(DOCSET_NAME)

.PHONY: package
package: $(DOCSET_PACKAGE)

$(DOCSET_PACKAGE): build
	tar --exclude='.DS_Store' --exclude='optimizedIndex.dsidx' -czf $(DOCSET_PACKAGE) $(DOCSET_DIR)

.PHONY: clean
clean:
	-rm -rf \
		$(DOCSET_DIR)/Contents/Resources/Documents/c \
		$(DOCSET_DIR)/Contents/Resources/docSet.dsidx \
		$(DOCSET_DIR)/Contents/Resources/optimizedIndex.dsidx \
		$(DOCSET_PACKAGE) \
		docset.json

ucd.nounihan.flat.xml: 
	curl -s -S -O https://www.unicode.org/Public/UCD/latest/ucdxml/ucd.nounihan.flat.zip
	unzip ucd.nounihan.flat.zip
	rm ucd.nounihan.flat.zip

cldr-annotations.json:
	curl -s -S -o $@ https://raw.githubusercontent.com/unicode-org/cldr-json/refs/heads/main/cldr-json/cldr-annotations-full/annotations/en/annotations.json
