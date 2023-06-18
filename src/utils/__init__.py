from subprocess import DEVNULL, PIPE, run

p = run(f'which pdftotext', shell=True, stdout=PIPE, stderr=DEVNULL) 
if p.stdout.decode() == "":
    raise RuntimeError("Command 'pdftotext' not found. Can be installed with apt install poppler-utils")