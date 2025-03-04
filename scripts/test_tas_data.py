import numpy as np
import os
import requests
import xarray
import pickle
import pandas as pd
import matplotlib.pyplot as plt

# the daily tas data is only from 1950 - opted to grab the 1850-1900
# baseline from ESGF

client = requests.session()

esms = [
    # 'ACCESS-CM2',
    # 'ACCESS-ESM1-5',
    # 'CanESM5',
    # 'CMCC-ESM2',
    # 'CNRM-CM6-1',
    # 'CNRM-ESM2-1',
    # 'EC-Earth3',
    # 'EC-Earth3-Veg-LR',
    # 'GFDL-ESM4',
    # 'GISS-E2-1-G',
    # 'INM-CM4-8',
    # 'INM-CM5-0',
    # 'IPSL-CM6A-LR',
    # 'KACE-1-0-G',
    'MIROC6',
    # 'MIROC-ES2L',
    # 'MPI-ESM1-2-HR',
    # 'MPI-ESM1-2-LR',
    # 'MRI-ESM2-0',
    # 'NorESM2-LM',
    # 'NorESM2-MM',
    # 'UKESM1-0-LL'
 ]

f2_models = ['CNRM-CM6-1', 'CNRM-ESM2-1', 'MIROC-ES2L', 'UKESM1-0-LL']

scen = 'ssp585'

cmip6_freqs = {
    "mon":"Amon",
    }

var = 'tas'
freq = 'mon'


nodes = ['https://esgf-data.dkrz.de/',  
         'https://esgf-node.ipsl.upmc.fr/', 'https://esg-dn1.nsc.liu.se/', 
         'https://esgf.nci.org.au/', 'https://esgf-node.ornl.gov/', 
         'https://esgf-node.llnl.gov/']#, 'https://esgf-index1.ceda.ac.uk/'] 


tas_1850_1900 = {}

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
  
        # search = '%sesg-search/search/?project=CMIP6&type=File&distrib=false&format=application%%2Fsolr%%2Bjson&experiment_id=%s&variable=%s&frequency=%s&source_id=%s&variant_label=r1i1p1f1' % (node, scen, var, freq, esm)

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

                    # # ie if 19th century, or file ends in 190 (for last file if annual or 5 yrly..)
                    # if cent == 8 or int(file.split("_")[-1
                    #      ].split("-")[1][:3]) == 190:
                    
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
        fnames = [fnames[0]]
        
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
    # weighted_mean.plot()
    
    
    tas_file = pd.read_csv(f'../data/essential/temperatures/csv/{esm}_{scen}_GMST.csv')
    
    # plt.plot(2015 + np.arange(86), tas_file.T.values[:,0], color = 'orange')#, label = 'Nasa')
    # plt.plot(2015 + np.arange(86), weighted_mean.values, color = 'blue')#, label = 'ESGF')
    # plt.legend()
    
    plt.plot(2015 + np.arange(86), weighted_mean.values - tas_file.T.values[:,0])#, label = 'ESGF')

    
    #%%

    
    weighted_mean_crop = weighted_mean.sel(time=slice(
        '1850-12-31T00:00:00.000000000', '1900-12-31T00:00:00.000000000'))
    
    if weighted_mean_crop.shape[0] != 51:
        raise Exception('Wrong time length')
    
    tas_1850_1900[esm] = float(weighted_mean_crop.mean('time').values)
    
    ds.close()
    
    
    # for f in fnames:
    #     os.remove(f)

#%%

with open('../data/essential/temperatures/pkl/tas_1850_1900.pkl', 'wb') as handle:
    pickle.dump(tas_1850_1900, handle, protocol=pickle.HIGHEST_PROTOCOL)

