from netCDF4 import Dataset
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.optimize import curve_fit
import copy

# run in base folder

DATADIR = 'data'
FIGDIR = 'plots'

years=np.arange(2020,2100,10)

varlist = ["PRCPTOT", "RX1D", "R50", "WD", "HW", "WN", "SPH", "CDHW"]
scens = ['ssp126', 'ssp245', 'ssp370', 'ssp585']
exposures = ['low', 'mean', 'high']

colors = {
    'ssp126':'#305590',
    'ssp245':'#21B8DD',
    'ssp370':'orange',
    'ssp585':'#D22128',
    }

data_dict = {}
for var in varlist:
    data_dict[var] = {}
    for scen in scens:
        data_dict[var][scen] = {}
        for exposure in exposures:
            data_dict[var][scen][exposure] = {}
            data_total = np.full(8, np.nan)
            data_per_person = np.full(8, np.nan)

            df_in = pd.read_csv(f'{DATADIR}/exposure/{var}.csv')
            data_exp = df_in[f"{scen}_{exposure}"]

            for y_i, year in enumerate(years):
                
                filein_pop = f'{DATADIR}/population/{scen[:4].upper()}_{year}.nc'
                data_pop = Dataset(filein_pop)
                
                data_total[y_i] = data_exp[y_i]
                data_per_person[y_i] = data_exp[y_i]/np.sum(data_pop.variables['Band1'][:])

                
            
            data_dict[var][scen][exposure]['Total'] = data_total
            data_dict[var][scen][exposure]['Per_person'] = data_per_person

    
    #%%

units = ['Total', 'Per_person']


for unit in units:
        
    fig, axs = plt.subplots(2, 4, figsize=(18, 10))
    
    for v_i, var in enumerate(varlist):
        axs = plt.subplot(2, 4, v_i+1)
        
        for scen in scens:
            
            axs.plot(years, data_dict[var][scen]['mean'][unit], 
                 color = colors[scen], linewidth=4, label=scen.upper())
            axs.fill_between(years, data_dict[var][scen]['low'][unit], 
                 data_dict[var][scen]['high'][unit], color = colors[scen], linewidth=0, alpha=0.2)
      
            axs.set_title(f'{var}')
            
        if v_i == 0 or v_i == 4:
            axs.set_ylabel(f'Exposure {unit}')
        
        if v_i ==7:
            axs.legend()

    plt.tight_layout()
    plt.savefig(
        f"{FIGDIR}/Exposure_{unit}.png"
    )
    plt.close()
    
#%%

esms = {
        "ACCESS-CM2":"r1i1p1f1",
        "ACCESS-ESM1-5":"r1i1p1f1",
        "CanESM5":"r1i1p1f1",
        "CMCC-ESM2":"r1i1p1f1",
        "CNRM-CM6-1":"r1i1p1f2",
        "CNRM-ESM2-1":"r1i1p1f2",
        "EC-Earth3":"r1i1p1f1",
        "EC-Earth3-Veg-LR":"r1i1p1f1",
        "GFDL-ESM4":"r1i1p1f1",
        "GISS-E2-1-G":"r1i1p1f2",
        "INM-CM4-8":"r1i1p1f1",
        "INM-CM5-0":"r1i1p1f1",
        "IPSL-CM6A-LR":"r1i1p1f1",
        "KACE-1-0-G":"r1i1p1f1",
        "MIROC6":"r1i1p1f1",
        "MIROC-ES2L":"r1i1p1f2",
        "MPI-ESM1-2-HR":"r1i1p1f1",
        "MPI-ESM1-2-LR":"r1i1p1f1",
        "MRI-ESM2-0":"r1i1p1f1",
        "NorESM2-LM":"r1i1p1f1",
        "NorESM2-MM":"r1i1p1f1",
        "UKESM1-0-LL":"r1i1p1f2",        
        }

mmm_temp = {}
mmm_temp['Years'] = years

full_temp = {}

temps_1850_1900 = {}
for esm in esms.keys():
    hist_tas_file = Dataset(f'{DATADIR}/temperatures/tas_ann_{esm}_historical_{esms[esm]}.nc')
    hist_tas_data = hist_tas_file.variables['tas'][:]
    
    tas_1850_1900 = np.mean(hist_tas_data[:100])
    temps_1850_1900[esm] = tas_1850_1900

for scen in scens:
    scen_data = np.full((len(esms), years.shape[0]), np.nan)
    for esm_i, esm in enumerate(esms.keys()):
        
        tas_file = Dataset(f'{DATADIR}/temperatures/tas_ann_{esm}_{scen}_{esms[esm]}.nc')

        tas_data = tas_file.variables['tas'][:] - temps_1850_1900[esm]

        for year_i, year in enumerate(years):
            y1_idx = 10*year_i
            y2_idx = y1_idx+10
            
            scen_data[esm_i, year_i] = np.mean(tas_data[y1_idx:y2_idx])
     
    mmm_temp[scen] = np.mean(scen_data, axis=0)
    full_temp[scen] = scen_data

    
#%%

for scen in scens:
    for esm_i, esm in enumerate(esms.keys()):
        plt.scatter(years, full_temp[scen][esm_i,:], 
                    color = 'grey', marker='o', s=5)
    plt.scatter(years, mmm_temp[scen], color = colors[scen],
                marker='o', zorder=2, label=f'{scen}')

plt.legend()
plt.ylabel('GMST cf 1850-1900')
   

plt.tight_layout()
plt.savefig(
    f"{FIGDIR}/GMSTs.png"
)
plt.close()  
   
#%%


    
fig, axs = plt.subplots(2, 4, figsize=(18, 10))

for v_i, var in enumerate(varlist):
    axs = plt.subplot(2, 4, v_i+1)
    
    for scen in scens:
        
        axs.scatter(mmm_temp[scen], data_dict[var][scen]['mean']['Per_person'], 
             color = colors[scen], label=scen.upper())
    
        axs.scatter(mmm_temp[scen], data_dict[var][scen]['low']['Per_person'], 
             color = colors[scen], s=5)
        
        axs.scatter(mmm_temp[scen], data_dict[var][scen]['high']['Per_person'], 
             color = colors[scen], s=5)
    
        axs.set_title(f'{var}')
        
    if v_i == 0 or v_i == 4:
        axs.set_ylabel('Exposure per person')
    
    if v_i >= 4:
        axs.set_xlabel('GMST')
    
    if v_i ==7:
        axs.legend()


plt.tight_layout()
plt.savefig(
    f"{FIGDIR}/Exposures_on_GMST.png"
)
plt.close()  
        
#%%

data_dict_sum = {}
for scen in scens:
    data_dict_sum[scen] = {}
    for exposure in exposures:
        data_dict_sum[scen][exposure] = np.zeros(8)
        
for var in varlist:
    for scen in scens:
        for exposure in exposures:
            data_dict_sum[scen][exposure] += data_dict[
                var][scen][exposure]['Per_person']


data_dict_sum_no_wn = {}
for scen in scens:
    data_dict_sum_no_wn[scen] = {}
    for exposure in exposures:
        data_dict_sum_no_wn[scen][exposure] = np.zeros(8)
        
for var in varlist:
    if var == 'WN':
        continue
    for scen in scens:
        for exposure in exposures:
            data_dict_sum_no_wn[scen][exposure] += data_dict[
                var][scen][exposure]['Per_person']

#%%

fig, axs = plt.subplots(1, 2, figsize=(10, 6))

axs = plt.subplot(1, 2, 1)

for scen in scens:
    
    axs.scatter(mmm_temp[scen], data_dict_sum[scen]['mean'], 
         color = colors[scen], label=scen.upper())
    
    axs.scatter(mmm_temp[scen], data_dict_sum[scen]['low'], 
         color = colors[scen], s=5)
    
    axs.scatter(mmm_temp[scen], data_dict_sum[scen]['high'], 
         color = colors[scen], s=5)

axs.set_title('Sum')
axs.legend()
axs.set_xlabel('GMST')
axs.set_ylabel('Per person exposure/yr')


axs = plt.subplot(1, 2, 2)

for scen in scens:
    
    axs.scatter(mmm_temp[scen], data_dict_sum_no_wn[scen]['mean'], 
         color = colors[scen], label=scen.upper())
    
    axs.scatter(mmm_temp[scen], data_dict_sum_no_wn[scen]['low'], 
         color = colors[scen], s=5)
    
    axs.scatter(mmm_temp[scen], data_dict_sum_no_wn[scen]['high'], 
         color = colors[scen], s=5)

axs.set_title('Sum w/o WN')
axs.legend()
axs.set_xlabel('GMST')
axs.set_ylabel('Per person exposure/yr')


plt.tight_layout()
plt.savefig(
    f"{FIGDIR}/Exposures_sum_on_GMST.png"
)
plt.close()  

#%%


def fit(x, a, beta_t, beta_t2):
    yhat = a + beta_t*x + beta_t2*x**2
    return yhat


gmst = 'data/AR6_GMST.csv'
gmst_in = pd.read_csv(gmst)


gmst_1970_1999 = np.mean(gmst_in[(1970 <= gmst_in['year']) & 
                     (gmst_in['year']<= 1999)]['gmst'])

gmst_offset = gmst_1970_1999
gmst_offset = 0

temps_plot = np.linspace(0, 4.5, 100)

exposure_colors = {
    
    'low':'blue', 
    'mean':'black', 
    'high':'red',
    }

data_dict_sum_no_wn_all_scens = {}
mmm_temp_all_scens = []
for scen in scens:
    mmm_temp_all_scens.append(mmm_temp[scen])
for exposure in exposures:
    data_dict_sum_no_wn_all_scens[exposure] = []
    for scen in scens:
        data_dict_sum_no_wn_all_scens[exposure].append(
            data_dict_sum_no_wn[scen][exposure])

params_dict = {}
for exposure in exposures:

    params_in, _ = curve_fit(
        fit, np.asarray(mmm_temp_all_scens).flatten() - gmst_offset, 
        np.asarray(data_dict_sum_no_wn_all_scens[exposure]).flatten())


    params_no_int = copy.deepcopy(params_in)

    params_no_int[0] = 0
    
    params_dict[exposure] = params_no_int
    

    plt.plot(temps_plot, fit(temps_plot, *params_no_int),
             label=f'{exposure}', color=exposure_colors[exposure])

    plt.plot(temps_plot, fit(temps_plot, *params_in),
             linestyle='dashed', color=exposure_colors[exposure])
    

    plt.scatter(np.asarray(mmm_temp_all_scens).flatten() - gmst_offset, 
        np.asarray(data_dict_sum_no_wn_all_scens[exposure]).flatten(), 
        color=exposure_colors[exposure])


plt.axhline(0, color='grey')
plt.legend()
plt.xlabel(f'GMST cf pi (offset: {np.around(gmst_offset, decimals=3)}K)')
plt.ylabel('Exposure (per person per year) cf pi \n (solid), absolute (dashed)')

 
plt.tight_layout()
# plt.savefig(
#     f"{FIGDIR}/Exposure_as_f_T.png", dpi=300
# )
# plt.close()         
        