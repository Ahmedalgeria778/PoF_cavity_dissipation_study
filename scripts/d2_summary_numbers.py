import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
base = os.path.join(os.path.dirname(HERE), "results", "09_d2_capture") + os.sep

meta = {}
for c in ['B1', 'B2', 'B3']:
    d = np.load(base + 'capture_' + c + '_D2_N256.npz', allow_pickle=True)
    m = json.loads(str(d['meta'].item()))
    meta[c] = m
    ce = d['cyc_eps']
    D = m['eps_cycle_mean']
    Dm = m['eps_meanfield']
    print(c)
    print('  Dbar =', D, ' Dmf =', Dm, ' fluct =', D - Dm, ' pct = %.1f' % (100 * (D - Dm) / D))
    print('  Kbar =', m['K_cycle_mean'], ' R_K =', m['R_K'], ' P/D =', m['P_cycle_mean'] / D)
    print('  Pmf =', m['P_meanfield'], ' K_mf =', m['K_meanfield'], ' K_fluct =', m['K_fluct'])
    print('  warm =', m['warm_periods'], ' drift =', m['drift'], ' liderr =', m['lid_max_error'])
    print('  half =', max(m['phase_half_diff']), ' sd =', float(np.std(ce)))
    print('  cyc_E mean =', float(np.mean(d['cyc_E'])), ' sd =', float(np.std(d['cyc_E'])))

D1 = meta['B1']['eps_cycle_mean']
D2v = meta['B2']['eps_cycle_mean']
D3 = meta['B3']['eps_cycle_mean']
print('ratios: B2/B1 = %.3f B2/B3 = %.3f B1/B3 = %.3f' % (D2v / D1, D2v / D3, D1 / D3))
