# JavaScript mutation pilot

Command: `just mutate-js --mutate src/tavle/static/dom.js,src/tavle/static/components/callout.js --disableBail`.

Stryker reported 130 mutants: 39 killed, 2 survived, 89 NoCoverage, 0 timeout and 0 errors. The mutation score was 30.00% (39 / 130); covered score was 95.12%. All 39 killed mutants were in `callout.js`; all 89 `dom.js` mutants had NoCoverage. The initial run passed 338 tests. This confirms related tests reach `callout.js`, but does not establish coverage for `dom.js` through the alias.

The JSON report contains `killedBy` entries; for example, a killed `callout.js` mutant has test IDs `["244", "246", "247", "249", "251", "252", "253"]`.

Stryker reported a wall time of 3 minutes 17 seconds. Peak memory: 1,684,936 KiB (about 1.6 GiB), the summed RSS of the run's process session sampled every 2 s in a lead rerun (`/usr/bin/time` is absent on this machine). Summed RSS counts shared pages more than once, so it is an upper estimate; the run stayed under the 4G `MUTATION_MEM` cap. The rerun took 3 minutes 4 seconds.

The standalone `dom.js` check stopped before mutation testing: `Vitest failed to find test files related to mutated files` and `No tests were executed. Stryker will exit prematurely.`
