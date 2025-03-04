# import subprocess
import numpy as np
import os 
import iris
import iris.analysis.cartography
import iris.coord_categorisation
import pandas as pd
import requests
import glob 

# from NASA, get the bias-corrected climate data used in the study
# this is only available from 1950

client = requests.session()

datadir = '../data'

esms = {
        'ACCESS-CM2': ['r1i1p1f1', 'gn'],
        'ACCESS-ESM1-5': ['r1i1p1f1', 'gn'],
        'CanESM5': ['r1i1p1f1', 'gn'],
        'CMCC-ESM2': ['r1i1p1f1', 'gn'],
        'CNRM-CM6-1': ['r1i1p1f2', 'gr'],
        'CNRM-ESM2-1': ['r1i1p1f2', 'gr'],
        'EC-Earth3': ['r1i1p1f1', 'gr'],
        'EC-Earth3-Veg-LR': ['r1i1p1f1', 'gr'],
        'GFDL-ESM4': ['r1i1p1f1', 'gr1'],
        'GISS-E2-1-G': ['r1i1p1f2', 'gn'],
        'INM-CM4-8': ['r1i1p1f1', 'gr1'],
        'INM-CM5-0': ['r1i1p1f1', 'gr1'],
        'IPSL-CM6A-LR': ['r1i1p1f1', 'gr'],
        'KACE-1-0-G': ['r1i1p1f1', 'gr'],
        'MIROC6': ['r1i1p1f1', 'gn'],
        'MIROC-ES2L': ['r1i1p1f2', 'gn'],
        'MPI-ESM1-2-HR': ['r1i1p1f1', 'gn'],
        'MPI-ESM1-2-LR': ['r1i1p1f1', 'gn'],
        'MRI-ESM2-0': ['r1i1p1f1', 'gn'],
        'NorESM2-LM': ['r1i1p1f1', 'gn'],
        'NorESM2-MM': ['r1i1p1f1', 'gn'],
        'UKESM1-0-LL': ['r1i1p1f2', 'gn'],
        }

years_future = 2015 + np.arange(86)
years_historical = 1950 + np.arange(51)

scens = {'ssp126':years_future,
         'ssp245':years_future,
         'ssp370':years_future,
         'ssp585':years_future,
         'historical':years_historical
         }

f_start = 'https://nex-gddp-cmip6.s3-us-west-2.amazonaws.com/NEX-GDDP-CMIP6/'


# missing_esms = []
for esm in esms.keys():
    print(esm)
    for scen in scens.keys():
        print(scen)
        
        if os.path.exists(f'{datadir}/essential/temperatures/csv/{esm}_{scen}_GMST.csv'):
            print('Already processed to csv')
            continue  
        
        years = scens[scen]
        
        df_out = pd.DataFrame(columns=[years])
        row = []
        
        for year in years:
            print(year)
            ripf = esms[esm][0]
            reg = esms[esm][1]
            
            fdir = f'{esm}/{scen}/{ripf}/tas/'
            fname = f'tas_day_{esm}_{scen}_{ripf}_{reg}_{year}.nc'
            
            url = f_start + fdir + fname

            
            if os.path.exists(f'{os.path.join(datadir, "essential", "temperatures", fname)}'):
                print('Downloaded already')
            else:       
                response = requests.get(url, stream=True)
                with open(os.path.join(datadir, 'essential', 'temperatures', fname), mode="wb") as fileout:
                    for chunk in response.iter_content(chunk_size = 500 * 1024):
                        fileout.write(chunk)
            
            cube = iris.load(os.path.join(datadir, 'essential', 'temperatures', fname))
            cube = cube.concatenate()[0]
            if not cube.coord('latitude').has_bounds():
                cube.coord('latitude').guess_bounds()
            if not cube.coord('longitude').has_bounds():
                cube.coord('longitude').guess_bounds()
            grid_areas = iris.analysis.cartography.area_weights(cube)
            cube_gm = cube.collapsed(['longitude', 'latitude', 'time'], iris.analysis.MEAN, weights=grid_areas)

        
            row.append(cube_gm.data)
            
            # os.remove(os.path.join(datadir, 'essential', 'temperatures', fname))

            
        
        df_out.loc[0] = row
        df_out.to_csv(f'{datadir}/essential/temperatures/csv/{esm}_{scen}_GMST.csv', index=False)
        
        nc_files = glob.glob(f'{datadir}/essential/temperatures/*nc')
        for nc_file in nc_files:
            os.remove(nc_file)
        

            
            
            # # For testing if exists
            # try:
            #     subprocess.check_output(f"wget --spider {f}", shell=True)
            # except subprocess.CalledProcessError as e:

            #     missing_esms.append(esm)

# print(set(missing_esms))


