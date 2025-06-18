# Developer guide

Information for contributors to the Gens project.

## Organization

 * assets -> The javascript files (rename?)
 * gens -> The Flask server
 * FastAPI

## The data flow

 * Raw data files accessed by Flask server
 * Passed through FastAPI (URL)
 * api.ts interacts exclusively with this URL
    * Caches many types of data
    * Zoom D - caches a range



## Development environment

```
npm install
npm run typecheck
npm run lint
npm run build ?
```
