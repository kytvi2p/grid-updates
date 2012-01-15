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
	@echo "$(APP) successfully installed to $(DESTDIR)$(PREFIX)"

installpatch:
	$(INSTALL) -d $(DATADIR)
	$(INSTALL_DATA) etc/webui/tahoe.css.patch etc/webui/welcome.xhtml.patch $(DATADIR)

clean:
	@rm -f README.html INSTALL.html MAN.html News/NEWS.html News/NEWS.tgz News/NEWS.atom

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

news:
	@sed -e '3,$$!d' -e '/^-\+$$/s/-/=/g' News/NEWS | \
		pandoc -s --template=News/pandoc-template.html -w html -r markdown --email-obfuscation=none > News/NEWS.html
	@sed -e "s/REPLACEUPDATED/$$(date +%FT%T%:z)/" -e "s/REPLACEDATE/$$(date -Ru)/" \
		-e "s/REPLACEID/urn:uuid$$(uuid)/" News/NEWS.atom.template > News/NEWS.atom
	@tar --directory News -c NEWS NEWS.html NEWS.atom | gzip -9 > News/NEWS.tgz

help:
	@echo "Type 'make install' to install grid-updates on your system."
	@echo "Type 'make man' to compile the manpage (requires 'pandoc')".
	@echo "Type 'make html' to compile HTML versions of the documentation."
	@echo "Type 'make release' to create a release tarball."

.PHONY: man viewman clean install help html tahoehtml news default installpatch
