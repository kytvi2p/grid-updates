default: help

PREFIX ?= /usr/local
BINDIR ?= $(PREFIX)/bin
MANDIR ?= $(PREFIX)/share/man/man1
DATAROOTDIR ?= $(PREFIX)/share
DATADIR= $(DATAROOTDIR)/$(APP)
APP= grid-updates
INSTALL= install
INSTALL_DATA= $(INSTALL) -m 644
MAN= man/grid-updates.1
PANDOC= pandoc -s -r rst -w html --email-obfuscation=none
TAHOE_DIR= http://127.0.0.1:3456/uri/URI%3ADIR2%3Anocmjemmatpn5yr4cfthvdvlxi%3Aeaqgy2gfsb73wb4f4z2csbjyoh7imwxn22g4qi332dgcvfyzg73a
VERSION= $$(git tag | tail -n 1 | sed s/v//)
RELEASE_BASENAME= grid-updates-$(VERSION)

install:
	@python setup.py install --prefix $(PREFIX)
	@echo "$(APP) successfully installed to $(DESTDIR)$(PREFIX)."

uninstall:
	@rm -vr $(BINDIR)/$(APP) $(MANDIR)/$(APP).1 $(DATADIR) $(DATADIR)/doc/$(APP)
	@echo "$(APP) successfully uninstalled."

clean:
	@rm -f README.html INSTALL.html MAN.html *.log *.pyc MANIFEST
	@rm -rf dist

man:
	pandoc -s -w man man/grid-updates.1.md -o $(MAN)
	@echo "Generated new manpage from markdown source."

viewman: man
	@man ./$(MAN)

html:
	@sed -e 's;\(INSTALL\\\?\)\.txt;\1.html;g' -e 's;man/grid-updates\.1\.md;MAN.html;' README.txt\
		| $(PANDOC) -o README.html
	@sed -e 's;\(README\\\?\)\.txt;\1.html;g' -e 's;man/grid-updates\.1\.md;MAN.html;' INSTALL.txt\
		| $(PANDOC) -o INSTALL.html
	@pandoc -s -r markdown -t html man/grid-updates.1.md -o MAN.html
	@echo "Generated HTML documentation from Markdown sources."

tahoehtml: html
	@mkdir -p tahoe-html
	@for file in README.html INSTALL.html MAN.html; \
		do \
		sed -e "s|\"\([INSTALL|README|MAN]\)|\"$(TAHOE_DIR)/\1|g" < $$file >  $$file.tmp ;\
		mv $$file.tmp tahoe-html/`basename $$file.tmp .tmp` ;\
		done
	@echo "Added links to Tahoe locations."

release: html
	@git archive --format=tar --prefix=$(RELEASE_BASENAME)/ --output $(RELEASE_BASENAME).tar v$(VERSION)
	@mkdir $(RELEASE_BASENAME)
	@mv INSTALL.html README.html MAN.html $(RELEASE_BASENAME)/
	@tar rf $(RELEASE_BASENAME).tar $(RELEASE_BASENAME)
	@gzip -9 $(RELEASE_BASENAME).tar
	@rm -r $(RELEASE_BASENAME)

help:
	@echo "Type 'make install' to install grid-updates on your system."
	@echo "Type 'make man' to compile the manpage (requires 'pandoc')".
	@echo "Type 'make html' to compile HTML versions of the documentation."
	@echo "Type 'make release' to create a release tarball."

lint:
	for f in *.py; \
		do \
		echo "$$f" ;\
		#pychecker "$$f" > "$$f".pychecker.log; \
		#pyflakes "$$f" > "$$f".pyflakes.log; \
		pylint "$$f" > "$$f".pylint.log; \
		done; \
		exit 0

dist: html
	python setup.py sdist --owner root --group root --formats gztar,zip

.PHONY: man viewman clean install help html tahoehtml default installpatch lint dist
