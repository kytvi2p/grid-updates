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
PANDOC= pandoc -s -r markdown -w html --email-obfuscation=none
TAHOE_DIR= http://127.0.0.1:3456/uri/URI%3ADIR2%3Anocmjemmatpn5yr4cfthvdvlxi%3Aeaqgy2gfsb73wb4f4z2csbjyoh7imwxn22g4qi332dgcvfyzg73a
VERSION= $$(git tag | tail -n 1)
RELEASE_BASENAME= grid-updates-$(VERSION)

install:
	$(INSTALL) -d $(DESTDIR)$(BINDIR) $(DESTDIR)$(MANDIR)
	$(INSTALL) $(APP) $(DESTDIR)$(BINDIR)
	$(INSTALL_DATA) $(MAN) $(DESTDIR)$(MANDIR)
	$(INSTALL) -d $(DATADIR)
	$(INSTALL_DATA) etc/tahoe.css.patch etc/welcome.xhtml.patch etc/NEWS.atom.template etc/pandoc-template.html $(DATADIR)
	@echo "$(APP) successfully installed to $(DESTDIR)$(PREFIX)."

uninstall:
	@rm -vr $(BINDIR)/$(APP) $(MANDIR)/$(APP).1 $(DATADIR)
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
	@sed -e 's;\(INSTALL\)\.md;\1.html;g' -e 's;man/grid-updates\.1\.md;MAN.html;' README.md \
		| $(PANDOC) -o README.html
	@sed -e 's;\(README\)\.md;\1.html;g' -e 's;man/grid-updates\.1\.md;MAN.html;' INSTALL.md \
		| $(PANDOC) -o INSTALL.html
	@$(PANDOC) man/grid-updates.1.md -o MAN.html
	@echo "Generated HTML documentation from Markdown sources."

tahoehtml:
	@sed -e 's;\(INSTALL\)\.md;\1.html;g' \
		-e "s;^\(\[INSTALL\.html\]:\ \)\(INSTALL\.html\);\1$(TAHOE_DIR)/\2;" \
		-e "s;^\(\[man\ page\]:\ \)man.grid-updates\.1\.md;\1$(TAHOE_DIR)/MAN.html;" README.md \
		| $(PANDOC) -o README.html
	@sed -e 's;\(README\)\.md;\1.html;g' \
		-e "s;^\(\[README\.html\]:\ \)\(README\.html\);\1$(TAHOE_DIR)/\2;" \
		-e "s;^\(\[man\ page\]:\ \)man.grid-updates\.1\.md;\1$(TAHOE_DIR)/MAN.html;" INSTALL.md \
		| $(PANDOC) -o INSTALL.html
	@$(PANDOC) man/grid-updates.1.md -o MAN.html
	@echo "Generated HTML documentation (with links to Tahoe locations) from Markdown sources."

release: html
	@git archive --format=tar --prefix=$(RELEASE_BASENAME)/ --output $(RELEASE_BASENAME).tar $(VERSION)
	@mkdir $(RELEASE_BASENAME)
	@mv INSTALL.html README.html MAN.html $(RELEASE_BASENAME)/
	@tar rf $(RELEASE_BASENAME).tar $(RELEASE_BASENAME)
	@gzip -c -9 $(RELEASE_BASENAME).tar > ../$(RELEASE_BASENAME).tgz
	@rm -r $(RELEASE_BASENAME) $(RELEASE_BASENAME).tar

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

dist:
	python setup.py sdist --owner root --group root --formats gztar,zip

.PHONY: man viewman clean install help html tahoehtml default installpatch lint dist
