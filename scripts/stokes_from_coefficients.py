import numpy as np, sys, json
sys.path.insert(0,"scripts")
import lid_command as L
RE=500.0; NU=1.0/RE; T=2.0
src={"B1":"data/lid_series/fourier_Re500.npz",
     "B2":"data/lid_series/B2_seed5_E025_re500_e0.25.npz",
     "B3":"data/lid_series/B3_seed0_E025_re500_e0.25.npz"}
MEAS={"B1":1.193424e-2,"B2":1.440819e-2,"B3":1.169011e-2}
DFL={"B1":2.149e-4,"B2":1.3392e-2,"B3":6.2775e-3}
for b,p in src.items():
    d=L.load_case(p,rescale_to=0.25); c=d["c"]
    # E_j = 1/4 sum_i c_ij^2 for j>=1 ; E_0 = 1/2 sum_i c_i0^2
    E0=0.5*float(np.sum(c[:,0]**2))
    Ej=0.25*np.sum(c[:,1:]**2,axis=0)
    om=np.arange(1,5)*np.pi
    Dst=float(np.sum(Ej*np.sqrt(NU*om/2.0)))
    delta=[float(np.sqrt(2.0*NU/(j*np.pi))) for j in range(1,5)]
    print(f"{b}: resid={d['resid']:.2e} E*={d['e_raw']:.9f} (E0+sumEj)={E0+Ej.sum():.9f}")
    print(f"   E_j = {np.array2string(Ej,precision=6,suppress_small=False)}")
    print(f"   D_St(coef exact)={Dst:.6e}   D_fluct(meas)={DFL[b]:.4e}  ratio meas/St={DFL[b]/Dst:.4f}")
    print(f"   Dbar_meas/D_St = {MEAS[b]/Dst:.4f}   delta_j(cells N=256) = {[round(x*256,2) for x in delta]}")
