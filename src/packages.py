from lxml import etree
import csv
import json
from glob import glob
from urllib.parse import urlparse
import operator

def extract_urls_from_sitemaps():
    url_set = set()
    f = glob('sitemaps/tools*.xml')
    for file in f:
        with open(file) as xml_file:
            tree = etree.parse(xml_file)
            root = tree.getroot()
            for url in tree.xpath("//*[local-name()='loc']/text()"):
                url_set.add(url)

    return url_set

def write_packages_csv():
    rows = []
    with open('prefixes.json') as prefix_file, open('packages.csv', 'w', newline='') as packages_csv:
        prefixes = json.load(prefix_file)
        packages_writer = csv.writer(packages_csv)
        packages_writer.writerow(['url', 'ecosystem'])

        for url in extract_urls_from_sitemaps():
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.split('/')

            package = None
            if path_parts and path_parts[1] and path_parts[1].split('-')[0] in prefixes:
                package = path_parts[1].split('-')[0]
                rows.append([url, package])

        sortedlist = sorted(rows, key=lambda x: (x[1],x[1]))
        packages_writer.writerows(sortedlist)

if __name__ == '__main__':
    write_packages_csv()