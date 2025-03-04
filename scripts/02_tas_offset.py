import numpy as np
import os
import requests
import xarray
import pickle

# the daily tas data is only from 1950, so to estimate the pre-industrial data
# we calculate the 1850-1900 to 1950-2000 difference with ESGF data, and then
# subtract from the 1950-2000 average in the NASA data.

client = requests.session()

esms = [
    'ACCESS-CM2',
    'ACCESS-ESM1-5',
    'CanESM5',
    'CMCC-ESM2',
    'CNRM-CM6-1',
    'CNRM-ESM2-1',
    'EC-Earth3',
    'EC-Earth3-Veg-LR',
    'GFDL-ESM4',
    'GISS-E2-1-G',
    'INM-CM4-8',
    'INM-CM5-0',
    'IPSL-CM6A-LR',
    'KACE-1-0-G',
    'MIROC6',
    'MIROC-ES2L',
    'MPI-ESM1-2-HR',
    'MPI-ESM1-2-LR',
    'MRI-ESM2-0',
    'NorESM2-LM',
    'NorESM2-MM',
    'UKESM1-0-LL'
 ]

f2_models = ['CNRM-CM6-1', 'CNRM-ESM2-1', 'MIROC-ES2L', 'UKESM1-0-LL']

scen = 'historical'

cmip6_freqs = {
    "mon":"Amon",
    }

var = 'tas'
freq = 'mon'


nodes = ['https://esgf-data.dkrz.de/',  
         'https://esgf-node.ipsl.upmc.fr/', 'https://esg-dn1.nsc.liu.se/', 
         'https://esgf.nci.org.au/', 'https://esgf-node.ornl.gov/', 
         'https://esgf-node.llnl.gov/']#, 'https://esgf-index1.ceda.ac.uk/'] 


tas_1850_1900_to_1950_2000 = {}

missing_esms = []

for esm in esms:
    print(esm)
    
    
    
    urls = []
    file_list = []


    for node in nodes:
        if len(file_list) > 0:
            continue

        print(node)
        client = requests.session()
  
        variant = 'r1i1p1f1'
        
        if esm in f2_models:
            variant = 'r1i1p1f2'

        search = f'{node}esg-search/search/?project=CMIP6&type=File&distrib=false&format=application%2Fsolr%2Bjson&experiment_id={scen}&variable={var}&frequency={freq}&source_id={esm}&variant_label={variant}&limit=1000'


        r = client.get(search)
        r.raise_for_status()
        resp = r.json()["response"]
        
        
        for d in resp["docs"]:
            for f in d["url"]:
                sp = f.split("|")
                # if sp[-1] == "OPENDAP":
                   
                wget_url = sp[0].split(".html")[0].replace("dodsC", "fileServer")
                file = wget_url.split("/")[-1]

                if file not in file_list:
                    
                    cent = int(file.split("_")[-1].split("-")[0][1])

                    # ie if 19th century, or file ends in 190 (for last file if annual or 5 yrly..)
                    if cent == 8 or cent == 9 or int(file.split("_")[-1
                         ].split("-")[0][:3]) == 200:
                        print('Found file')                            
                        file_list.append(file)
                        # print(file)
                        urls.append(wget_url)
     
    if len(file_list) == 0:
        missing_esms.append(esm)
                 
    fnames = []
    
    for url in urls:
        
        
        fname = url.split("/")[-1]
        
        fnames.append(fname)
        
        if os.path.exists(fname) == True:
            continue

        response = requests.get(url, stream=True)

        with open(fname, mode="wb") as fileout:
            for chunk in response.iter_content(chunk_size = 500 * 1024):
                fileout.write(chunk)
               
                
               
    if esm == 'GISS-E2-1-G': # weired doubling up files with this model
        fnames = [f for f in fnames if 'Amon_GISS-E2-1-G' in f] # sometimes get extra freqs..
        
    fnames = [f for f in fnames if 'Amon' in f] # sometimes get extra freqs..

                    
    ds = xarray.open_mfdataset(fnames)


    if type(ds.indexes['time']) == xarray.coding.cftimeindex.CFTimeIndex:
            
        datetimeindex = ds.indexes['time'].to_datetimeindex()
        ds['time'] = datetimeindex
        
    tas = ds.tas
    
    tas = tas.resample(time="YE").mean()
    
    weights = np.cos(np.deg2rad(tas.lat))
    weights.name = "weights"
    
    tas_weighted = tas.weighted(weights)
    
    weighted_mean = tas_weighted.mean(("lon", "lat"))

    
    weighted_mean_crop_pi = weighted_mean.sel(time=slice(
        '1850-12-31T00:00:00.000000000', '1900-12-31T00:00:00.000000000'))
    
    if weighted_mean_crop_pi.shape[0] != 51:
        raise Exception('Wrong time length')
    
    
    weighted_mean_crop_recent = weighted_mean.sel(time=slice(
        '1950-12-31T00:00:00.000000000', '2000-12-31T00:00:00.000000000'))
    
    if weighted_mean_crop_recent.shape[0] != 51:
        raise Exception('Wrong time length')
    
    
    tas_1850_1900_to_1950_2000[esm] = float(weighted_mean_crop_recent.mean('time').values
                                            ) - float(weighted_mean_crop_pi.mean('time').values)
                                                                                    
    
    ds.close()
    
    for f in fnames:
        os.remove(f)

#%%

with open('../data/essential/temperatures/pkl/tas_1850_1900_to_1950_2000.pkl', 'wb') as handle:
    pickle.dump(tas_1850_1900_to_1950_2000, handle, protocol=pickle.HIGHEST_PROTOCOL)

