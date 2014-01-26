# Static site builder for existing lessons


## Install

- Python 2, with pyyaml
- Pandoc (a recent version)
- Phantomjs

## Configure

In build.py at the top you can see where the legal text, organization name, logo, and css variables are set.

## Running

Check out the project repositories somewhere locally, including CodeClubWorld-Projects, CodeClubUK-Projects

```
./build.sh world <path to python repository> <path to scratch repository> ... <world output repository>
./build.sh uk <path to python repository> <path to scratch repository> ... <uk output repository>
```

It copies /assets over, then copies /templates/css over, replacing ${variables} inside.
Then it scans for JSON manifest files inside the source repositories, and then builds a list of these
by language.

It then creates /<lang-code>/<term>-<num>/<project num>/<project files> for each project and ancillary data,
creating indexes by language, term, too.

lessons should follow the markdown syntax described in an accompanying file
manifests should already be built, and hopefully self descriptive (example included too)

## Testing

Run a webserver in the output directory, e.g.

```
$ python -m SimpleHTTPServer <port>
```

