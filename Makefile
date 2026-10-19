sitemaps/tools.xml:
	python src/fetch_sitemap.py
clean:
	rm -f sitemaps/*.xml packages.csv tools.csv
packages.csv: sitemaps/tools.xml
	python src/packages.py
tools.csv: packages.csv
	python src/tools.py
