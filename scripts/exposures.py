from netCDF4 import Dataset
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

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

# esms = ["ACCESS-CM2", "ACCESS-ESM1-5", "CanESM5", "CMCC-ESM2", "CNRM-CM6-1", 
#         "CNRM-ESM2-1", "EC-Earth3", "EC-Earth3-Veg-LR", "GFDL-ESM4", 
#         "GISS-E2-1-G", "INM-CM4-8", "INM-CM5-0", "IPSL-CM6A-LR", "KACE-1-0-G", 
#         "MIROC6", "MIROC-ES2L", "MPI-ESM1-2-HR", "MPI-ESM1-2-LR", "MRI-ESM2-0",
#         "NorESM2-LM", "NorESM2-MM", "UKESM1-0-LL"]


esms = ["ACCESS-CM2"]

mmm_temp = {}

for scen in scens:
    scen_data = np.full((len(esms), years.shape[0]), np.nan)
    for esm_i, esm in enumerate(esms):
        df_in = pd.read_csv(f'{DATADIR}/temperatures/{esm}_{scen}_GMST.csv')
        df_t = df_in.T
        df_t.columns = ['Temperature']
        df_t.index = df_t.index.astype(int)
        
        for year_i, year in enumerate(years):
            
            scen_data[esm_i, year_i] = np.mean(df_t[(df_t.index>=year-5) & 
                                       (df_t.index<year+5)].values)
     
    mmm_temp[scen] = np.mean(scen_data, axis=0)
            
        
    