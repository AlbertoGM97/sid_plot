# sid_plot - Plotter for supersid files

Based on the SuperSID project (see https://github.com/ericgibert/supersid) sid_plot is an attempt to provide a simple plotter script for supersid files.

Developed in python3 over matplotlib.

## Available options
```sh
usage: python3 sid_plot.py file1.csv file2.csv [Options]

optional arguments:
  -h, --help            show this help message and exit
  -f, --filter          Filter with moving average
  -o OUT_FILE, --out OUT_FILE
                        Output imgage to file (default svg). For automatic date name type
                        '-o %'. NOTE:'-o' option implies '-n'
  -p, --png             Use png image format (instead of svg)
  -n, --nodisp          Dont output to screen
  -w, --web             Add NOAA XRA events
  -t, --time            Add timestamp on image (UTC hour)
  -s, --std             Hide station with standard deviation below threshold
  ```