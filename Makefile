version=`date +%Y.%-m.%-d`

sitemaps/tools4.xml: sitemaps/tools3.xml
	wget -P sitemaps --quiet --timestamping https://stackshare.io/sitemaps/tools4.xml
sitemaps/tools3.xml: sitemaps/tools2.xml
	wget -P sitemaps --quiet --timestamping https://stackshare.io/sitemaps/tools3.xml
sitemaps/tools2.xml: sitemaps/tools.xml
	wget -P sitemaps --quiet --timestamping https://stackshare.io/sitemaps/tools2.xml
sitemaps/tools.xml:
	wget -P sitemaps --quiet --timestamping https://stackshare.io/sitemaps/tools.xml
clean:
	rm -f sitemaps/*.xml packages.csv tools.csv
packages.csv: sitemaps/tools4.xml
	python src/packages.py
tools.csv: packages.csv
	python src/tools.py
	echo "::set-output name=version::$(version)"