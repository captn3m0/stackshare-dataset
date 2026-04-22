version=`date +%Y.%-m.%-d`

sitemaps/tools.xml:
	wget -P sitemaps --timestamping https://stackshare.io/sitemap/tools.xml
clean:
	rm -f sitemaps/*.xml packages.csv tools.csv
packages.csv: sitemaps/tools.xml
	python src/packages.py
tools.csv: packages.csv
	python src/tools.py
	echo "::set-output name=version::$(version)"