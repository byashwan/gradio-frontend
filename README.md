# FastAPI Example on Cloudfoundry: Intel Workweek Finder

Basic app to deploy a 'hello world' API to CloudFoundry.

When running, the API can be accessed at: https://intelcalendar.apps1-fm-int.icloud.intel.com/

Docs: https://intelcalendar.apps1-fm-int.icloud.intel.com/docs

## What this API does
This API does one thing: it returns the current Intel year and workweek in YYYYWW format.

## Steps applied:
* Added bash scripts (cf_login and cf_push) and config file (cf_config) for easier cloudfoundry stuff.
* added manifest.yml to tell cloudfoundry what kind of instance to set up
* added .cfignore and .gitignore to ignore stuff like __pycache__

* Procfile - you need to set --host=0.0.0.0 or it'll do a localhost by default

* runtime.txt - this file is optional, I use it to specify the type of Python to use (i.e. 3.8.x)

## Automatic Docs

Once deployed it goes up and it works at the address specified. You can use the `/docs` or `/redoc` to get cool docs right off the bat.

