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
#DOCCOMPILER= pandoc -s -r rst -w html --email-obfuscation=none -o
DOCCOMPILER= rst2html -
TAHOE_DIR= /uri/URI%3ADIR2-RO%3Ahgh5ylzzj6ey4a654ir2yxxblu%3Ahzk3e5rbsefobeqhliytxpycop7ep6qlscmw4wzj5plicg3ilotq
##VERSION= $$(git tag | tail -n 1 | sed s/v//)
VERSION= $$(python -c "from gridupdates.version import __version__; print __version__")
RELEASE_BASENAME= grid-updates-$(VERSION)

install:
	@python setup.py install --prefix $(PREFIX)
	@echo "$(APP) successfully installed to $(DESTDIR)$(PREFIX)."

uninstall:
	@rm -vr $(BINDIR)/$(APP) $(MANDIR)/$(APP).1 $(DATADIR) $(DATADIR)/doc/$(APP)
	@echo "$(APP) successfully uninstalled."

clean:
	@rm -f README.html INSTALL.html MAN.html MANIFEST
	@rm -rf gridupdates/__pycache__
	@find . \( -name "*\.py[co]" -o -name "*\.log" \) -exec rm -f {} \;
	@rm -rf dist tahoe-html
	@rm -f tahoehtml-stamp html-stamp dist-stamp man-stamp

man: man-stamp

man-stamp:
	pandoc -s -w man man/grid-updates.1.md -o $(MAN)
	@echo "Generated new manpage from markdown source."
	@touch $@

viewman: man
	@man ./$(MAN)

html: html-stamp
html-stamp:
	@sed -e 's;\(INSTALL\\\?\)\.txt;\1.html;g' -e 's;man/grid-updates\.1\.md;MAN.html;' README.txt\
		| $(DOCCOMPILER) README.html
	@sed -e 's;\(README\\\?\)\.txt;\1.html;g' -e 's;man/grid-updates\.1\.md;MAN.html;' \
		-e "s|\$$ver|$(VERSION)|" INSTALL.txt | $(DOCCOMPILER) INSTALL.html
	@sed -e 's|see\ below|see <a href="#header">above</a>|' man/grid-updates.1.md | \
		pandoc --email-obfuscation=none -s -r markdown -t html -o MAN.html
	@sed -e '5,$$s|\(http://[:a-zA-Z0-9._/-]\{1,\}\)|<a href="\1">\1</a>|g' < MAN.html > MAN.html.tmp
	@sed -e 's|\(Trac ticket #1799\)|<a href="https://tahoe-lafs.org/trac/tahoe-lafs/ticket/1799">\1</a>|' < MAN.html.tmp > MAN.html
	@rm MAN.html.tmp
	@echo "Generated HTML documentation from Markdown sources."
	@touch $@

tahoehtml: html tahoehtml-stamp

tahoehtml-stamp:
	@mkdir -p tahoe-html
	@for file in README.html INSTALL.html MAN.html; \
		do \
		sed -e "s|\(href=\"\)\([INSTALL|README|MAN]\)|\1$(TAHOE_DIR)/\2|g" < $$file >  $$file.tmp ;\
		mv $$file.tmp tahoe-html/`basename $$file.tmp .tmp` ;\
		done
	@sed -e 's|http\://127\.0\.0\.1\:3456||g' tahoe-html/README.html > tahoe-html/README.html.tmp
	@mv tahoe-html/README.html.tmp tahoe-html/README.html
	@sed -e 's|\(URI:[A-Za-z0-9.:_/-]\{1,\}\)|<a href="/uri/\1">\1</a>|g' < tahoe-html/MAN.html > tahoe-html/MAN.html.tmp
	@mv tahoe-html/MAN.html.tmp tahoe-html/MAN.html
	@echo "Added links to Tahoe locations."
	@touch $@

##release: html
##	@git archive --format=tar --prefix=$(RELEASE_BASENAME)/ --output $(RELEASE_BASENAME).tar v$(VERSION)
##	@mkdir $(RELEASE_BASENAME)
##	@mv INSTALL.html README.html MAN.html $(RELEASE_BASENAME)/
##	@tar rf $(RELEASE_BASENAME).tar $(RELEASE_BASENAME)
##	@gzip -9 $(RELEASE_BASENAME).tar
##	@rm -r $(RELEASE_BASENAME)

help:
	@echo "Type 'make install' to install grid-updates on your system."
	@echo "Type 'make man' to compile the manpage (requires 'pandoc')".
	@echo "Type 'make html' to compile HTML versions of the documentation."
	@echo "Type 'make release' to create a release tarball."

lint:
	for f in *.py gridupdates/*.py; \
		do \
		echo "$$f" ;\
		#pychecker "$$f" > "$$f".pychecker.log; \
		#pyflakes "$$f" > "$$f".pyflakes.log; \
		pylint "$$f" > "$$f".pylint.log; \
		done; \
		exit 0

dist: html man dist-stamp

dist-stamp:
	python setup.py sdist --owner root --group root --formats gztar,zip
	@touch $@

.PHONY: man viewman clean install help html tahoehtml default installpatch lint dist
