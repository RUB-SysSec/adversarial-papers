import json
import re
import shutil
from pathlib import Path

import pandas as pd

PAPER_LENGTH = {
    # ieee s&p
    "2202.09470": 8259,
    "2108.06504": 11764,
    "2112.03570": 7950,
    "2104.02739": 5487,
    "2112.05719": 8703,
    "2101.11073": 6010,
    "2112.04838": 7468,
    "2108.09528": 6393,
    "2108.10241": 8432,
    "2108.13818": 6236,
    "2112.05588": 8027,
    "2104.08638": 9627,
    "2112.07498": 6466,
    "2107.04284": 8613,
    "2010.12450": 7535,
    "2106.09898": 7371,
    "2111.04625": 7838,
    "2112.05224": 7032,
    "2108.09293": 7052,
    "2108.00352": 7775,
    "2107.07065": 10193,
    "2010.03856": 8031,
    "2112.03449": 6902,
    "2108.09454": 4051,
    "2108.01341": 9438,
    "2201.04845": 9212,
    "2112.05307": 6387,
    "2105.05801": 7416,
    "2112.01967": 6343,
    "2110.12340": 7711,
    "2112.08331": 8372,
    "2112.09014": 6660,
    # usenix:
    "1807.00477" : 8723,
    "1808.04761" : 5975,
    "1811.02054" : 8933,
    "1812.00891" : 9743,
    "1903.00503" : 8859,
    "1904.01067" : 6740,
    "1904.02033" : 6952,
    "1904.03542" : 7816,
    "1904.06278" : 6558,
    "1905.10311" : 6834,
    "1906.03969" : 7887,
    "1908.01405" : 7610,
    "1908.02444" : 8210,
    "1908.03296" : 6478,
    "1908.07000" : 7138,
    "1909.01838" : 6806,
    "1909.09599" : 8220,
    "1911.05673" : 6995,
    "1911.11815" : 7790,
    "1911.12834" : 6733,
    "1912.00317" : 9023,
    "1912.01701" : 8303,
    "1912.10190" : 7426,
    "1912.11118" : 7218,
    "2001.04107" : 7463,
    "2003.00572" : 9426

}

class Trial:

    def __init__(self, trial_dir=None, label=None, only_featurespace=False):

        if trial_dir is None:
            return
    
        self.label = label
        self.trial_dir = trial_dir
        self.data = []
        self.config = {}
        self.log = {}
        self.transformers = {}

        self.export_list = []
        self.failed = []

        for log_file in self.trial_dir.rglob('log.txt'):
            
            # files
            results_file = log_file.with_name('results.json')
            config_file = log_file.with_name('config.json')
            feature_space_results = list(log_file.parent.joinpath('itrs').rglob('feature_space_results*.json'))

            # finished?
            if (not results_file.is_file() and not only_featurespace) or \
               (len(feature_space_results) == 0 and only_featurespace):
                continue
            
            try:
                feature_space_results = sorted(feature_space_results, key=lambda x: int(x.stem.split('_')[-1]))[-1]
                # load
                config = json.loads(config_file.read_text())
                applied_transformers =  None if only_featurespace else json.loads(feature_space_results.parent.with_name('applied_transformers.json').read_text())
                results = None if only_featurespace else json.loads(results_file.read_text())
                feature_space_results = json.loads(feature_space_results.read_text())            
                log = log_file.read_text()
            except Exception as e:
                print("[!] Exception occured")
                import traceback
                print(traceback.format_exc())
                continue

            # exclude trivial attacks in stats
            if len([ r for r in feature_space_results['successful'] if r is not None]) == 0:
                continue

            try:
                ranks = list(results['ranks'][0]['request'].values())[0]
            except:
                ranks = None
            
            r = {
                'name' : log_file.parent.name,
                'no_request' : len(config['target']['request']),
                'no_reject' : len(config['target']['reject']),
                'running_time' : 0 if only_featurespace else results['running_time'],
                'p_successful' : 0 if only_featurespace else len([ r for r in results['successful'] if r == True]),
                'p_failed' : 0 if only_featurespace else len([ r for r in results['successful'] if r == False]), 
                'p_invalid' : 0 if only_featurespace else len([ r for r in results['successful'] if r is None]),
                'p_l1' : 0 if only_featurespace else results['l1'],
                'p_l1_frac' : 0 if only_featurespace else results['l1'] / PAPER_LENGTH[Path(config['submission']).name],
                'p_linf' : 0 if only_featurespace else results['linf'],
                'f_no_itr' : len(re.findall(r'\[\s*(\d+)\]', log)),
                'f_l1' : min(feature_space_results['l1']),
                'f_linf' : min(feature_space_results['linf']),
                'f_successful' : len([ r for r in feature_space_results['successful'] if r == True]),
                'f_failed' : len([ r for r in feature_space_results['successful'] if r == False]), 
                'f_invalid' : len([ r for r in feature_space_results['successful'] if r is None]),
                'switches' : 0 if only_featurespace else results['feature_problem_switch'],
                'ranks' : ranks
            }

            if not only_featurespace:
                for victim_idx in range(len(results['successful'])):
                    r[f'p_successful_{victim_idx}'] = results['successful'][victim_idx]

            self.data += [r] 

            if r['p_failed'] > 0:
                self.failed += [ log_file.parent ]

            # keep config
            self.config[log_file.parent.name] = config
            self.log[log_file.parent.name] = log_file
            self.transformers[log_file.parent.name] = applied_transformers

        self.data = pd.DataFrame(self.data)

    @property
    def is_empty(self):
        return len(self.data) == 0 

    def __str__(self):
        if len(self.data) == 0:
            return f"{self.label.upper()}\n    n/a"
        format_runtime = lambda runtime: f'{runtime // 3600:.0f}h {(runtime % 3600) // 60:2.0f}m {(runtime % 60):2.0f}s'
        df = pd.DataFrame(
            [
                [ 'Success       '     , f'{self.data.f_successful.sum():.0f} / {self.data.f_successful.sum() + self.data.f_failed.sum():.0f}',  
                                         f'{self.data.p_successful.sum():.0f} / {self.data.p_successful.sum() + self.data.p_failed.sum():.0f}'],
                [ 'Finished'           , f'{self.data.running_time.count()}',  f''],
                [ 'Running Time   Mean', f'{format_runtime(self.data.running_time.mean())}',  f''],
                [ '             Median', f'{format_runtime(self.data.running_time.median())}',  f''],
                [ '                Max', f'{format_runtime(self.data.running_time.max())}',  f''],
                [ '     Mean'          , f'{self.data.f_l1.mean():4.0f}',
                                         f'{self.data.p_l1.mean():4.0f}', ],
                [ '   Median'          , f'{self.data.f_l1.median():4.0f}',
                                         f'{self.data.p_l1.median():4.0f}', ],
                [ '      Max'          , f'{self.data.f_l1.max():4.0f}',
                                         f'{self.data.p_l1.max():4.0f}', ],
                [ '      Min'          , f'{self.data.f_l1.min():4.0f}',
                                         f'{self.data.p_l1.min():4.0f}', ],
                [ 'Linf   Mean'        , f'{self.data.f_linf.mean():4.0f}',
                                         f'{self.data.p_linf.mean():4.0f}'],
                [ '     Median'        , f'{self.data.f_linf.median():4.0f}',
                                         f'{self.data.p_linf.median():4.0f}'],
                [ 'Switches Min'       , f'{self.data.switches.min():4.0f}', f''],
                [ 'Switches Max'       , f'{self.data.switches.max():4.0f}', f''],
                [ 'Switches Median'    , f'{self.data.switches.median():4.0f}', f''],

            ],
            columns=['Metric', 'Feature Space', 'Problem Space']
        )
        return f"[+] {self.label.upper()}\n" + "\n".join([ f"    {l}" for l in df.to_string(index=False).splitlines() ])

    def __len__(self):
        return len(self.data)
    
    def export_failed(self):
        SUBMISSIONS_BASE_DIR = Path.home().joinpath('adversarial-papers', 'evaluation', 'submissions')
        MODELS_BASE_DIR = Path.home().joinpath('adversarial-papers', 'evaluation', 'models')
        export_dir = Path.home() / "adversarial-papers" / "evaluation" / "trials" / "_failed" / self.label
        if export_dir.is_dir():
            print(f"[!] Export dir already exists '{export_dir}'")
            if input("    Enter yes to overwrite: ") == 'yes':
                print(f'    -> removed dir')
                shutil.rmtree(export_dir)
            else:
                return
        export_dir.mkdir(parents=True)
        # export targets
        targets = []
        for run_dir in self.failed:
            config = json.loads(run_dir.joinpath('config.json').read_text())
            target = {
                'submission' : Path(config['submission'].replace("/root", Path.home().as_posix())).relative_to(SUBMISSIONS_BASE_DIR).as_posix(),
                'target_reviewer' : config['target'],
                'victim_models' : [ Path(model_dir.replace("/root", Path.home().as_posix())).relative_to(MODELS_BASE_DIR).as_posix() for model_dir in config['victim_model_dirs'] ],
                'surrogate_models' : [ Path(model_dir.replace("/root", Path.home().as_posix())).relative_to(MODELS_BASE_DIR).as_posix() for model_dir in config['surrogate_model_dirs'] ],
                'problemspace_config' : config['problemspace_config'],
                'featurespace_config' : config['featurespace_config'],
            }
            target['problemspace_config'] = { k : v for k, v in target['problemspace_config'].items()
                                                    if not (isinstance(v, str) and v.startswith('/home')) }
            targets += [target]


        export_dir.joinpath('targets.json').write_text(json.dumps(targets, indent=4))
        # copy run
        print(f'[+] copy runs')
        for run_dir in self.failed:
            print(f'    {run_dir.name}')
            shutil.copytree(run_dir, export_dir.joinpath('runs', run_dir.name))
        # zip
        print(f'[+] zip')
        shutil.make_archive(export_dir.as_posix(), 'zip', export_dir.as_posix())
        shutil.move(export_dir.with_suffix('.zip').as_posix(), export_dir.as_posix())

    def export(self):
        SUBMISSIONS_BASE_DIR = Path.home().joinpath('adversarial-papers', 'evaluation', 'submissions')
        MODELS_BASE_DIR = Path.home().joinpath('adversarial-papers', 'evaluation', 'models')
        export_dir = Path.home() / "adversarial-papers" / "evaluation" / "trials" / "_export" / self.label
        if export_dir.is_dir():
            print(f"[!] Export dir already exists '{export_dir}'")
            if input("    Enter yes to overwrite: ") == 'yes':
                print(f'    -> removed dir')
                shutil.rmtree(export_dir)
            else:
                return
        export_dir.mkdir(parents=True)
        # export targets
        targets = []
        for run_dir in self.export_list:
            config = json.loads(run_dir.joinpath('config.json').read_text())
            target = {
                'submission' : Path(config['submission'].replace("/root", Path.home().as_posix())).relative_to(SUBMISSIONS_BASE_DIR).as_posix(),
                'target_reviewer' : config['target'],
                'victim_models' : [ Path(model_dir.replace("/root", Path.home().as_posix())).relative_to(MODELS_BASE_DIR).as_posix() for model_dir in config['victim_model_dirs'] ],
                'surrogate_models' : [ Path(model_dir.replace("/root", Path.home().as_posix())).relative_to(MODELS_BASE_DIR).as_posix() for model_dir in config['surrogate_model_dirs'] ],
                'problemspace_config' : config['problemspace_config'],
                'featurespace_config' : config['featurespace_config'],
            }
            target['problemspace_config'] = { k : v for k, v in target['problemspace_config'].items()
                                                    if not (isinstance(v, str) and v.startswith('/home')) }
            targets += [target]


        export_dir.joinpath('targets.json').write_text(json.dumps(targets, indent=4))
        # copy run
        print(f'[+] copy runs')
        for run_dir in self.export_list:
            print(f'    {run_dir.name}')
            shutil.copytree(run_dir, export_dir.joinpath('runs', run_dir.name))
        # zip
        print(f'[+] zip')
        shutil.make_archive(export_dir.as_posix(), 'zip', export_dir.as_posix())
        shutil.move(export_dir.with_suffix('.zip').as_posix(), export_dir.as_posix())
