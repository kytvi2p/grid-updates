default: help

PREFIX ?= /usr/local
BINDIR ?= $(PREFIX)/bin
MANDIR ?= $(PREFIX)/share/man/man1
APP= grid-updates
INSTALL= install
INSTALL_DATA= $(INSTALL) -m 644

install:
	$(INSTALL) -d $(DESTDIR)$(BINDIR) $(DESTDIR)$(MANDIR)
	$(INSTALL) $(APP) $(DESTDIR)$(BINDIR)
	$(INSTALL_DATA) man/grid-updates.1 $(DESTDIR)$(MANDIR)
	@echo "$(APP) successfully installed to $(DESTDIR)$(PREFIX)"


clean:
	@-rm -f man/grid-updates.1

man:
	pandoc -s -w man man/grid-updates.1.md -o man/grid-updates.1
	@echo "Generated new manpage from markdown source."

view: man
	@man ./man/grid-updates.1

help:
	@echo "Type 'make man' to compile the manpage (requires 'pandoc')".
	@echo "Type 'make install' to install grid-updates on your system."

.PHONY: man view clean install help default
