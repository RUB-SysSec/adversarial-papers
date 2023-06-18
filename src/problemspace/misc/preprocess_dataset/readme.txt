This directory contains a script to run 'latexpand' on a collected dataset
Assumptions:
- datasetdir has the following structure:
  datasetdir
      paper1
      paper2
      paper3
      ...
In each paper directory, the latex files are located.
Each paper directory can have an arbitrary name, in our case, it is the arxiv number

Script assumes that main latex file with 'main document' is somewhere located in paper directory without any subdirs.
It will try to automatically find it. If there are too many choices, it raises an exception.

Output:
latexpand is necessary to
- get files without comments, (they could create problems for automatic transformations)
- get files with all includes, as we can only rewrite the main file currently.
Furthermore:
- the main document file (e.g. 'paper.tex') will be renamed into 'main.tex' together will all 'main.*' files,
unless there are already other 'main.*' files. In this way, each main document files as root file has same name.

Steps:
0. Download latexpand
    - https://gitlab.com/latexpand/latexpand
1. copy example_config_latexpand.ini to config_latexpand.ini and
2. adjust paths there
    - config_latexpand.ini is in gitignore, so that we do not mess up with the configuration of other users
3. run run_latexpand.py
    - run script as long as exceptions are thrown. Fix them, delete target dir and run script again.
4. After that, go to `problemspace/misc/test_compilation_dataset` and run further compilation checks!