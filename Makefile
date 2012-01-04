default: help

PREFIX ?= /usr/local
BINDIR ?= $(PREFIX)/bin
MANDIR ?= $(PREFIX)/share/man/man1
APP= grid-updates
INSTALL= install
INSTALL_DATA= $(INSTALL) -m 644
PANDOC= pandoc -s -r markdown -w html
TAHOE_DIR= http://127.0.0.1:3456/uri/URI%3ADIR2%3Anocmjemmatpn5yr4cfthvdvlxi%3Aeaqgy2gfsb73wb4f4z2csbjyoh7imwxn22g4qi332dgcvfyzg73a

install:
	$(INSTALL) -d $(DESTDIR)$(BINDIR) $(DESTDIR)$(MANDIR)
	$(INSTALL) $(APP) $(DESTDIR)$(BINDIR)
	$(INSTALL_DATA) man/grid-updates.1 $(DESTDIR)$(MANDIR)
	@echo "$(APP) successfully installed to $(DESTDIR)$(PREFIX)"


clean:
	@rm -f README.html INSTALL.html MAN.html

man:
	pandoc -s -w man man/grid-updates.1.md -o man/grid-updates.1
	@echo "Generated new manpage from markdown source."

viewman: man
	@man ./man/grid-updates.1

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

help:
	@echo "Type 'make install' to install grid-updates on your system."
	@echo "Type 'make man' to compile the manpage (requires 'pandoc')".
	@echo "Type 'make html' to compile HTML versions of the documentation."

.PHONY: man viewman clean install help html tahoehtml default
