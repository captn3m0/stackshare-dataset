# stackshare-dataset [![DOI](https://zenodo.org/badge/747065915.svg)](https://zenodo.org/doi/10.5281/zenodo.10554436)

**DOI**: `10.5281/zenodo.10554437`

A dataset from stackshare.io providing lists of packages and various services. While a list of packages for
various ecosystems is easily available elsewhere, a list of services is much harder.

See `tools.csv` for a complete list. I'd recommend sorting by populatity and using the top 2.5-3k results
depending on your usecase.

Browse the dataset here: <https://flatgithub.com/captn3m0/stackshare-dataset?filename=tools.csv&sort=popularity%2Cdesc&stickyColumnName=url>.

## License

This stackshare-dataset is made available under the Open Database License: http://opendatacommons.org/licenses/odbl/1.0/. 
Some individual contents of the database are under copyright by Stackshare.

You are free:

* **To share**: To copy, distribute and use the database.
* **To create**: To produce works from the database.
* **To adapt**: To modify, transform and build upon the database.

As long as you:

* **Attribute**: You must attribute any public use of the database, or works produced from the database, in the manner specified in the ODbL. For any use or redistribution of the database, or works produced from it, you must make clear to others the license of the database and keep intact any notices on the original database.
* **Share-Alike**: If you publicly use any adapted version of this database, or works produced from an adapted database, you must also offer that adapted database under the ODbL.
* **Keep open**: If you redistribute the database, or an adapted version of it, then you may use technological measures that restrict the work (such as DRM) as long as you also redistribute a version without such measures.


## Generating

Ensure you have GNU Make, Python, and wget installed

```
make tools.csv
make packages.csv
```

The scraper uses the following as sources:

1. Sitemap (https://stackshare.io/sitemap.xml)
2. StackShare Search for enriching service results (https://stackshare.io/search)

The package results are not enriched, since much better data for those is available elsewhere.