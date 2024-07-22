# import subprocess
import numpy as np
import os 
import iris
import iris.analysis.cartography
import iris.coord_categorisation
import pandas as pd
import glob

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

years = 2015 + np.arange(86)

scens = ['ssp126', 'ssp245', 'ssp370', 'ssp585']

f_start = 'https://nex-gddp-cmip6.s3-us-west-2.amazonaws.com/NEX-GDDP-CMIP6/'


# missing_esms = []
for esm in esms.keys():
    print(esm)
    for scen in scens:
        print(scen)
        
        if os.path.exists(f'outputs/{esm}_{scen}_GMST.csv'):
            continue        
        
        df_out = pd.DataFrame(columns=[years])
        row = []
        
        for year in years:
            print(year)
            ripf = esms[esm][0]
            reg = esms[esm][1]
            
            fdir = f'{esm}/{scen}/{ripf}/tas/'
            fname = f'tas_day_{esm}_{scen}_{ripf}_{reg}_{year}.nc'
            
            f = f_start + fdir + fname

            
            if os.path.exists(f'{fname}'):
                print('Downloaded already')
            else:       
                os.system(f'wget {f} .')
            
            cube = iris.load(fname)
            cube = cube.concatenate()[0]
            if not cube.coord('latitude').has_bounds():
                cube.coord('latitude').guess_bounds()
            if not cube.coord('longitude').has_bounds():
                cube.coord('longitude').guess_bounds()
            grid_areas = iris.analysis.cartography.area_weights(cube)
            cube_gm = cube.collapsed(['longitude', 'latitude', 'time'], iris.analysis.MEAN, weights=grid_areas)

        
            row.append(cube_gm.data)
#            print(f'Data: {row}')

#            os.system(f'rm -f {f}')
        
        df_out.loc[0] = row
        df_out.to_csv(f'outputs/{esm}_{scen}_GMST.csv', index=False)
        
        #os.system('rm -f *nc')
        nc_files = glob.glob('*nc')
        for nc_file in nc_files:
            os.remove(nc_file)
        

            
            
            # # For testing if exists
            # try:
            #     subprocess.check_output(f"wget --spider {f}", shell=True)
            # except subprocess.CalledProcessError as e:

            #     missing_esms.append(esm)

# print(set(missing_esms))


