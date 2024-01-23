sitemaps/tools4.xml: sitemaps/tools3.xml
	wget -P sitemaps --quiet --timestamping https://stackshare.io/sitemaps/tools4.xml
sitemaps/tools3.xml: sitemaps/tools2.xml
	wget -P sitemaps --quiet --timestamping https://stackshare.io/sitemaps/tools3.xml
sitemaps/tools2.xml: sitemaps/tools.xml
	wget -P sitemaps --quiet --timestamping https://stackshare.io/sitemaps/tools.xml
sitemaps/tools.xml:
	wget -P sitemaps --quiet --timestamping https://stackshare.io/sitemaps/tools.xml
packages.csv: sitemaps/tools4.xml
	python src/packages.py
tools.csv: packages.csv
	python src/tools.py