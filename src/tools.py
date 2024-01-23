import http.client
import csv
import json
from urllib.parse import urlparse
import os
import urllib.parse
from math import floor
from packages import extract_urls_from_sitemaps

HEADERS = ['url', 'object_id', 'name', 'title', 'popularity', 'votes', 'verified', 'description', 'stack_count', 'type', 'category', 'layer', 'function']
conn = http.client.HTTPSConnection("km8652f2eg-dsn.algolia.net")

def tools_except_packages():
    all_tools = extract_urls_from_sitemaps()
    packages = set()
    with open('packages.csv') as packages_file:
        for row in csv.reader(packages_file):
            packages.add(row[0])
    return all_tools - packages

def make_request(search):
    payload = {
      "query": search,
      "hitsPerPage": 3,
      "filters": "NOT type:Stackup"
    }
    payload = json.dumps(payload)

    headers = {
        'Accept': "application/json",
        'Accept-Encoding': "deflate",
        "Content-Type": "application/json"
    }

    conn.request("POST", "/1/indexes/Search_production/query?x-algolia-application-id=KM8652F2EG&x-algolia-api-key=YzFhZWIwOGRhOWMyMjdhZTI5Yzc2OWM4OWFkNzc3ZTVjZGFkNDdmMThkZThiNDEzN2Y1NmI3MTQxYjM4MDI3MmZpbHRlcnM9cHJpdmF0ZSUzRDA%3D", payload, headers)

    res = conn.getresponse()
    data = res.read()
    d = json.loads(data.decode("utf-8"))
    if len(d['hits']) >= 1:
        for x in d['hits']:
            if x['canonical_url'] == search:
                return x
                break
    else:
        print(f"MISS: {search}")

def get_row(ignore_set):
        for url in tools_except_packages():
            if url in ignore_set:
                continue
            data = make_request(urlparse(url).path)
            if data and data['is_package'] == False:
                yield [
                    url,
                    data['objectID'],
                    data['name'],
                    data['title'],
                    data['popularity'],
                    data['votes_count'],
                    data['verified'],
                    data['description'],
                    data['company_stacks_count'],
                    data['type'].lower(),
                    data['category']['slug'],
                    data['layer'].lower(),
                    data['function']['slug']
                ]

if __name__ == '__main__':
    if not os.path.exists('tools.csv'):
        with open('tools.csv', 'w', newline='') as of:
            writer = csv.writer(of)
            writer.writerow(HEADERS)

    urls_written = set()
    with open('tools.csv') as tools_file:
        for row in csv.reader(tools_file):
            urls_written.add(row[0])

    with open('tools.csv', 'a', newline='') as of:
        writer = csv.writer(of)
        for row in get_row(urls_written):
            writer.writerow(row)

    # Sort the tools.csv file by 4th column (popularity)
    with open('tools.csv', 'r') as f:
        reader = csv.reader(f)
        next(reader, None) # skip the header
        sortedlist = sorted(reader, key=lambda row: float(row[4]), reverse=True)
    with open('tools.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)
        writer.writerows(sortedlist)