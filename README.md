# Static site builder for existing lessons


## Install

- Python 2, with pyyaml
- Pandoc (a recent version)
- Phantomjs

## Running

Check out the project repositories somewhere locally.

```
./build.sh <path to python repository> <path to scratch repository> ... <output_directory>
```

## Testing

Run a webserver in the output directory, e.g.

```
$ python -m SimpleHTTPServer
```

