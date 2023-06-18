import configparser
import pathlib
import shutil
import sys
import subprocess

### Settings: Read config.ini to get all path information
__config_ini_file_path = pathlib.Path.cwd() / "problemspace" / "misc" / "preprocess_dataset" / "config_latexpand.ini"
assert __config_ini_file_path.exists()
config = configparser.ConfigParser()
config.read(__config_ini_file_path)

datasetdir = pathlib.Path(config['DATASET']['datasetdir'])
targetdir = pathlib.Path(config['DATASET']['targetdir'])
latexpandcmdpath = config['LATEXPAND']['latexpandcmdpath']

latexpand_fullcmd = pathlib.Path(latexpandcmdpath)


def runlatexpand(latexpand_cmd, latexfilename, latexsourcedir, targetfile):
    cmd = [latexpand_cmd, latexfilename]
    p = subprocess.run(cmd, stdout=open(targetfile, 'w'),
                       stderr=subprocess.PIPE, shell=False, timeout=120,
                       cwd=str(latexsourcedir))
    errx = p.stderr
    if errx != b'':
        print(
            f"Error/Warning: {errx} for {latexsourcedir}. If warning that latexpand does not find file, "
            f"it might be due to if-else latex cmd. Check output file", file=sys.stderr)
    if not p.returncode == 0:
        raise Exception(
            'Latexpand: Executing error {} with command: {}'.format(p.returncode, ' '.join(cmd)))


### Preprocessing: Iterate over all files, copy them to target dir and run latexpand
assert datasetdir.exists()
if not targetdir.exists():
    print(f"Create target dir at {targetdir}")
    targetdir.mkdir()

for pathobject in datasetdir.glob("*"):
    if pathobject.is_dir():

        # A. Copy
        targetprojectdir: pathlib.Path = targetdir / pathobject.name
        if targetprojectdir.exists():
            print(f"Target dir exists at {targetprojectdir}")
            raise FileExistsError()
        shutil.copytree(pathobject, targetprojectdir)

        # B. Find main file
        # bbl file is only used to propose main file in case of error
        bbl_file: int = 0
        bbl_name = None
        for latexfile in targetprojectdir.glob("*.bbl"):
            bbl_file += 1
            bbl_name = latexfile.name  # will be the last matched one, so careful...

        main_file: int = 0
        main_file_name = None
        main_file_stem = None
        for latexfile in targetprojectdir.glob("*.tex"):
            if "documentclass[" in latexfile.read_text():
                main_file += 1
                main_file_name = latexfile.name  # will be the last matched one, so careful...
                main_file_stem = latexfile.stem

        if main_file == 0:
            raise Exception(f"For {targetprojectdir} NO main file detected in project dir")
        elif main_file >= 2:
            err = f"For {targetprojectdir} TOO MANY main files detected in project dir"
            if bbl_file >= 2:
                err += f"\n\t I've also found {bbl_file} bbl files"
            elif bbl_file == 1:
                err += f"\n\t I assume that main file is >>{bbl_name.replace('.bbl', '.tex')}<<"

            raise Exception(err)

        print(f"Success for {targetprojectdir}: Main file found: {main_file_name}")

        # C. run latexpand
        target_tempfilepath = targetprojectdir / ('temp_' + main_file_name)
        runlatexpand(latexpand_cmd=latexpand_fullcmd,
                       latexfilename=main_file_name, latexsourcedir=targetprojectdir, targetfile=target_tempfilepath)

        if not target_tempfilepath.exists():
            raise Exception(f"For {targetprojectdir} target_tempfile DOES NOT exist")
        if not target_tempfilepath.stat().st_size > 0:
            raise Exception(f"For {targetprojectdir} target_tempfile has SIZE = 0")

        # D. rename, clean
        if main_file_name == "main.tex":
            # just rename target file back to original file name, so that we can use all temporary files, such as bbl
            shutil.move(target_tempfilepath, targetprojectdir / main_file_name)
        else:
            # we want that main document file is main.tex, so rename temp file to main.tex, and rename all other files
            mainflx = [latexfile for latexfile in targetprojectdir.glob("main.*")]
            if len(mainflx) > 0:
                raise Exception("There are other main.* files in project dir. Cannot overwrite")
            shutil.move(target_tempfilepath, targetprojectdir / main_file_name)
            for latexfile in targetprojectdir.glob(main_file_stem + ".*"):
                shutil.move(latexfile, targetprojectdir / ("main" + latexfile.suffix))
