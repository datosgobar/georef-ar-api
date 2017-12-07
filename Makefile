doctoc: ## generate table of contents, doctoc command line tool required
        ## https://github.com/thlorenz/doctoc
        ## hay que ir al documento y manualmente agregar un espacio entre los
        ## comentarios especiales de doctoc y el --title para que se vea bien
	doctoc --title "## Indice" README.md
	bash fix_github_links.sh docs/api_reference.md
