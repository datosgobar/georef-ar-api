.PHONY: docs

docs:
	mkdocs build
	$(BROWSER) site/index.html

servedocs:
	mkdocs serve

# Generar tablas de contenidos, se requiere el comando 'doctoc'
# https://github.com/thlorenz/doctoc
doctoc:
	doctoc --maxlevel 3 --github --title " " docs/quick_start.md
	bash docs/fix_github_links.sh docs/quick_start.md
	doctoc --maxlevel 3 --github --title " " docs/spreadsheet_integration.md
	bash docs/fix_github_links.sh docs/spreadsheet_integration.md
	doctoc --maxlevel 3 --github --title " " docs/python_usage.md
	bash docs/fix_github_links.sh docs/python_usage.md
	doctoc --maxlevel 3 --github --title " " docs/jwt-token.md
	bash docs/fix_github_links.sh docs/jwt-token.md
	doctoc --maxlevel 3 --github --title " " docs/developers/georef-api-development.md
	bash docs/fix_github_links.sh docs/developers/georef-api-development.md
	doctoc --maxlevel 3 --github --title " " docs/developers/python3.6.md
	bash docs/fix_github_links.sh docs/developers/python3.6.md
	doctoc --maxlevel 3 --github --title " " docs/developers/georef-api-data.md
	bash docs/fix_github_links.sh docs/developers/georef-api-data.md
