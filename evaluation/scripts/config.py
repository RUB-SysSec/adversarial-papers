import matplotlib
import matplotlib.pyplot as plt
from pathlib import Path

matplotlib.rcParams['text.usetex'] = True
matplotlib.rcParams['mathtext.fontset'] = 'stix'
matplotlib.rcParams['font.family'] = 'STIXGeneral'
matplotlib.pyplot.title(r'ABC123 vs $\mathrm{ABC123}^{123}$')

BASE_DIR = Path.home().joinpath('/root/adversarial-papers')
DATA_DIR =  BASE_DIR.joinpath('evaluation/trials/')
PLOTS_DIR = BASE_DIR.joinpath('evaluation/plots')
MODELS_DIR = BASE_DIR.joinpath('evaluation/models')

PLOTS_DIR.mkdir(exist_ok=True, parents=True)

colors = { 
    'green' : '#798376',
    'darkgreen' : '#484E46',
    'blue' : '#41678B',
    'darkblue' : '#2D4861',
    'orange' : '#CB9471',
    'darkorange' : '#965B37',
    'red' : '#B65555',
    'mint' : '#6AA56E',
    'grey' : '#616161',
    'lightgrey' : '#EEEEEEEE'

}

colors_idxes = list(colors)

def format_running_time(running_time, long=False):
    if long:
        return f'{running_time // 3600:.0f}h {(running_time % 3600) // 60:.0f}m {(running_time % 60):.0f}s'
    return f'{running_time // 60:.0f}m {(running_time % 60):.0f}s'