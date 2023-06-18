
from pathlib import Path
import sys
sys.path.append(Path.home().joinpath('adversarial-papers', 'src').as_posix())  

import json
from autobid import AutoBid
import numpy as np
from collections import Counter

SUBMISSIONS_DIR = Path.home().joinpath('adversarial-papers', 'evaluation', 'submissions', 'oakland_22')

linf = {}
submission_length = {}
for submission in SUBMISSIONS_DIR.joinpath('pdf_compiled').glob('*.pdf'):
    words = AutoBid.parse_pdf_file(submission)
    submission_length[submission.stem] = len(words)
    linf[submission.stem] = np.linalg.norm(list(Counter(words).values()), np.inf)
    print(f"[+] {submission.stem}: {len(words)}")
    print(f"    {linf[submission.stem]}")

SUBMISSIONS_DIR.joinpath('submission_length.json').write_text(json.dumps(submission_length, indent=4))
SUBMISSIONS_DIR.joinpath('linf.json').write_text(json.dumps(linf, indent=4))

print(f'[+] Linf   (mean): {np.mean(list(linf.values()))}')
print(f'[+] Length (mean): {np.mean(list(submission_length.values()))}')