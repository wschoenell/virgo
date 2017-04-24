
# coding: utf-8

# Code to make a script to download the spectra from SDSS:

# In[44]:

import os
import numpy as np
from astropy.io import fits
from scipy import sparse


# In[16]:

tab = fits.getdata("virgo_william.fit")


# In[5]:

wget_list = ["wget -c https://dr12.sdss.org/sas/dr12/sdss/spectro/redux/26/spectra/%04d/spec-%04d-%d-%04d.fits\n" % (v["plate"], v["plate"], v["mjd"], v["fiberID"]) for v in tab]


# In[6]:

with open("wget_spec.sh", "w") as fp:
    fp.writelines(wget_list)


# After spectra is donwnloaded, calculate magnitudes

# In[17]:

from syntphot import photoconv
from readfilterset import FilterSet


# In[18]:

f = FilterSet("splus_herpich.hdf5")
f.load("splus", 1)


# In[29]:

magnitudes = np.zeros((len(tab), len(f.filter_wls)))
specobjids = np.zeros(len(tab), dtype=np.int)


# In[38]:

for i_gal, gal in enumerate(tab):
    specobjids[i_gal] = tab[i_gal]['specObjID']
    magnitudes[i_gal] = photoconv().fromSDSSfits(f.filterset, "spec/spec-%04d-%d-%04d.fits" % (v["plate"], v["mjd"], v["fiberID"]))['m_ab']


# In[40]:

specobjids[:2], magnitudes[:2]


# In[55]:

try:
    os.unlink("jplus_mags.csv")
except OSError:
    pass
np.savetxt("jplus_mags.csv", np.column_stack((specobjids[:,np.newaxis],magnitudes)), delimiter=',', fmt='%i ' + len(f.filter_wls) * "%6.3f ", header="specobjid " + " ".join(f.filter_wls["ID_filter"]) * 2 )


# In[11]:




# In[27]:

print magnitudes[i_gal]


# In[54]:




# In[ ]:



