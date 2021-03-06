'''
Created on Jul 17, 2012

@author: william
'''

import numpy as np

def spec2filter(filter, obs_spec, model_spec=None, badpxl_tolerance = 0.5):
    '''
    Converts a spectrum on AB magnitude given a filter bandpass.

    If there are bad pixels on filter interval on a fraction inferior to the badpxl_tolerance, it will
    interpolate the missing values or, in case of a model_spec is not None, it will use the values from model_spec.

    Parameters
    ----------
    filter : dict
             Filter transmission curve. Dictionary containing the following entries:
             {'wl': array_like
                    Wavelength (in Angstroms!).
             'transm': array_like
                          Filter transmission response.
             }

    obs_spec : dict
               Observed Spectra. Dictionary containing the following entries:
                 {'wl': array_like,
                  'flux': array_like, 
                  'error': array_like, optional,
                  'flag': array_like, optional,
                  'model_spec': array_like, optional
                  }

    model_spec : dict, optional
                 Model Spectra which could be used when there are missing (due to err or flagged). Dictionary containing the following entries:
                   {    'wl': array_like
                              Wavelength (in the same units as filter response curve)
                        'flux': array_like
                                Flux on a given wl
                   }

    badpxl_tolerance : float, default: 0.5
                       Bad pixel fraction tolerance on the spectral interval of the filter.
    
    Returns
    -------
    m_ab : float
           AB magnitude on given filter
    e_ab : float 
           AB magnitude error on given filter
           
    See Also
    --------
    
    Notes
    -----

    '''
    #Cut the spectrum on the filterset range. This improves the velocity of the rest of the accounts.
    obs_cut = obs_spec[np.bitwise_and(obs_spec['wl'] >= np.min(filter['wl']), obs_spec['wl'] <= np.max(filter['wl']))]
    
    if model_spec is not None:
        model_cut = model_spec[np.bitwise_and(model_spec['wl'] >= np.min(filter['wl']), model_spec['wl'] <= np.max(filter['wl']))]
        if len(model_cut) == 0:
            #log.warning('No enough MODEL datapoints eval synthetic photometry on this filter. Model will NOT be considered.')
            model_spec = None
        elif np.any(model_cut['wl'] != obs_cut['wl']):
            #log.warning('Model is not sampled the same way as the observed spectrum. Interpolating...')
            aux = np.copy(model_cut)
            # model_cut = obs_cut[:len(model_spec)].copy()
            model_cut = np.zeros(len(obs_cut), dtype=model_cut.dtype)
            model_cut['wl'] = obs_cut['wl']
            model_cut['flux'] = np.interp(obs_cut['wl'],aux['wl'],aux['flux'], left=0.0, right=0.0)
    #Check if the filterset is sampled correctly
    #  - Tip: Resample the filter to your data when reading the filter to avoid unnessessary interpolations. 
    if np.any(obs_cut['wl'] != filter['wl']):
        # log.warning('Filter is not sampled the same way as the observed spectrum. Interpolating...')
        wl_ = obs_cut['wl']
        transm_ = np.interp(wl_,filter['wl'],filter['transm'])
    else:
        wl_ = filter['wl']
        transm_ = filter['transm']

    
    #Check for bad pixels. Good pixels should be signaled with flag(lambda) = 0 or 1.
    # The recipe is: 
    #    - If there is LESS bad_pixels than badpxl_tolerance:
    #        And there is a model_spec: use model_spec
    #        And there is NOT a model_spec: interpolate values
    #    - If there is MORE bad_pixels than badpxl_tolerance:
    #        Return a magnitude np.inf and an error of np.inf. 
    n = len(obs_cut)
    not_neg_pix = (obs_cut['flux'] >= 0) #Fluxes CAN NOT be negative! NEVER!!!!! 
    if('flag' in obs_cut.dtype.names and 'error' in obs_cut.dtype.names): # First check if there is error AND flag.
        good    = np.bitwise_and(np.bitwise_and(obs_cut['flag'] <= 1, obs_cut['error'] > 0), not_neg_pix)
        bad     = np.invert(good)
        n_bad   = np.sum(bad)
    elif('error' in obs_cut.dtype.names): # Check if there is ONLY error.
        good    = np.bitwise_and(obs_cut['error'] > 0, not_neg_pix)
        bad     = np.invert(good)
        n_bad   = np.sum(bad)
    elif('flag' in obs_cut.dtype.names): # Check if there is ONLY flag.
        good    = np.bitwise_and(obs_cut['flag'] <= 1, not_neg_pix)
        bad     = np.invert(good)
        n_bad   = np.sum(bad)
    else: # If there is only spectra, all the pixels are good! =)
        good    = np.bitwise_and(obs_cut['wl'] > 0, not_neg_pix)
        bad     = np.invert(good)
        n_bad   = np.sum(bad)
    print( 'N_points: %d, N_bad: %d' % (n, n_bad) )
    
    
    if(n_bad > 0 or n == 0): #If we have problems we have to deal with them... ;)
        if (n == 0):
            print('# of pixels = 0. m = inf and m_err = inf')
            m_ab = np.inf
            e_ab = np.inf
            return m_ab, e_ab
        p_bad = np.float(n_bad)/np.float(len(obs_cut))
        if(p_bad > badpxl_tolerance): #If we have # of bad pixels greater than 50%, then make filter flux and error equal to inf.
            print('# of bad pixels > badpxl_tolerance. m = inf and m_err = inf')
            m_ab = np.inf
            e_ab = np.inf
            return m_ab, e_ab
        else:
            #If we have # of bad pixels less than 50%, we simply neglect this point on the error acoounts,
            #and make flux = synthetic flux, if available, if not, interpolate values.
            if model_spec is not None:
                obs_cut['flux'][bad] = model_cut['flux'][bad]
            else: 
                obs_cut['flux'][bad] = np.interp(obs_cut['wl'][bad], obs_cut['wl'][good], obs_cut['flux'][good])

    else: # If our observed obs_spec is ALL ok. =)
        print('No bad pixel! =)')
    m_ab = -2.5 * np.log10( np.trapz(obs_cut['flux'] * transm_ * wl_, wl_)  / np.trapz(transm_ / wl_, wl_) ) - 2.41

    if('error' in obs_cut.dtype.names):
        e_ab = 1.0857362047581294 * np.sqrt( np.sum(transm_[good]**2 * obs_cut['error'][good]**2 * wl_[good] ** 2 )) / np.sum(obs_cut['flux'][good] * transm_[good] * wl_[good])
    else:
        e_ab = 0.0

    return m_ab, e_ab

def spec2filterset(filterset, obs_spec, model_spec = None, badpxl_tolerance = 0.5):
    '''
    Run spec2filter over a filterset

    Parameters
    ----------
    filterset : object
                Filter transmission curves (see: magal.io.readfilterset).

    obs_spec : dict
               Observed Spectra. Dictionary containing the following entries:
                 {    'wl': array_like
                            Wavelength. (in Angstroms!)
                      'flux': array_like 
                              Flux on a given wl.
                      'error': array_like, optional
                               Flux error. If err < 0, the point will be considered as a problem. 
                      'flag': array_like, optional
                              Bad pixel flag. Pixels are considered bad if flag > 1.
                      'model_spec': array_like, optional
                                    Model Spectra which could be used when there are missing (due to err or flagged). 
                  }
                  
    model_spec : dict, optional
                 Model Spectra which could be used when there are missing (due to err or flagged). Dictionary containing the following entries:
                   {    'wl': array_like
                              Wavelength (in the same units as filter response curve)
                        'flux': array_like
                                Flux on a given wl
                   }
    badpxl_tolerance : float, default: 0.5
                       Bad pixel fraction tolerance on the spectral interval of the filter.
                      
    Returns
    -------
    mags : array_like
           Filterset magnitudes
           Dictionary containing the following entries:
             {
                'm_ab': array_like
                        AB magnitude on given filter.
                'e_ab' : array_like
                         AB magnitude error on given filter.
            }
           
    See Also
    --------
    spec2filter, magal.io.readfilterset.FilterSet
    
    Notes
    -----

    '''
    filter_ids = np.unique(filterset['ID_filter'])
    mags = np.zeros(len(filter_ids), dtype = np.dtype([('m_ab', '<f4'), ('e_ab', '<f4')]))
    for i_filter in range(len(filter_ids)):
        filter = filterset[filterset['ID_filter'] == filter_ids[i_filter]]
        mags[i_filter]['m_ab'], mags[i_filter]['e_ab'] = spec2filter(filter, obs_spec, model_spec, badpxl_tolerance = badpxl_tolerance)
        print('Magnitude to filter %s: %3.2f, error: %3.2f' % (filter_ids[i_filter], mags[i_filter]['m_ab'], mags[i_filter]['e_ab']) )
    return mags

class photoconv(object):
    """
    Spectrum to Photometry conversion class.
    """

    def fromStarlight(self, filterset, arq_in, arq_syn, starlight_version='starlightv4', badpxl_tolerance=0.5):
        """
        Converts automagically STARLIGHT input and output files into photometric magnitudes
        
        Parameters
        ----------
        filterset : object
            Filter transmission curves (see: magal.io.readfilterset).
        arq_in : string
            Starlight input filename (or atpy.TableSet(type='starlight_input') object)
        arq_syn : string
            Starlight synthesis filename (or atpy.TableSet(type=starlight_version) object)
        starlight_version : string, default = 'starlightv4'
            Starlight synthesis file version (Default: starlightv4)
        badpxl_tolerance : float, default: 0.5
            Bad pixel fraction tolerance on the spectral interval of each filter. (Default: 0.5)
        
        Returns
        -------
        m_ab : numpy.ndarray dtype = [('m_ab', '<f4'), ('e_ab', '<f4')]
        
        See Also
        --------
        fromSDSSfits, magal.io.readfilterset
        
        """
        
        try:  # Try to import pystarlight...
            import pystarlight.io
            import atpy
        except ImportError:
            print('Exception! Could not load pystarlight. Needed to convert from STARLIGHT')
        
        try:  # Check if it is an atpy or a filename
            obs_spec = arq_in.starlight_input.data.view(
                dtype=np.dtype([('wl', '<f8'), ('flux', '<f8'), ('error', '<f8'), ('flag', '<i8')]))
        except AttributeError:
            arq_in = atpy.Table(arq_in, type='starlight_input')
            obs_spec = arq_in.data.view(
                dtype=np.dtype([('wl', '<f8'), ('flux', '<f8'), ('error', '<f8'), ('flag', '<i8')]))
        
        try:  # Check if it is an atpy or a filename
            model_spec = arq_syn.spectra.data.view(dtype=np.dtype(
                [('wl', '<f8'), ('f_obs', '<f8'), ('flux', '<f8'), ('f_wei', '<f8'), ('Best_f_SSP', '<f8')]))
        except AttributeError:
            arq_syn = atpy.TableSet(arq_syn, type=starlight_version)
            model_spec = arq_syn.spectra.data.view(dtype=np.dtype(
                [('wl', '<f8'), ('f_obs', '<f8'), ('flux', '<f8'), ('f_wei', '<f8'), ('Best_f_SSP', '<f8')]))

        obs_spec['flux'] *= 1e-17
        obs_spec['error'] *= 1e-17
        model_spec['flux'] *= arq_syn.keywords['fobs_norm'] * 1e-17
        
        
        return spec2filterset(filterset, obs_spec, model_spec, badpxl_tolerance = badpxl_tolerance)

    def fromSDSSfits(self, filterset, fits, badpxl_tolerance = 0.5):
        ''' Converts automagically SDSS .fits spectrum files into photometric magnitudes
        
        Parameters
        ----------
        filterset : string or object
                    Filterset filename (or magal.io.readfilterset object)
        fits : string or object 
               SDSS .fits filename (or atpy.basetable.Table object)
        badpxl_tolerance : float 
                           Bad pixel fraction tolerance on the spectral interval of each filter. (Default: 0.5)
        
        
        Returns
        -------
        m_ab: numpy.ndarray dtype = [('m_ab', '<f8'), ('e_ab', '<f8')]
        
        See Also
        --------
        fromStarlight
        
        '''
        
        try:  # Try to import atpy
            import atpy
        except ImportError:
            print('Exception! Could not load atpy. Needed to convert from SDSS fits files')

        try:  # Is it already a atpy table?
            fits.data['loglam'] = 10 ** fits.data['loglam']
            self.obs_spec = fits.data.view(dtype=np.dtype(
                [('flux', '>f4'), ('wl', '>f4'), ('error', '>f4'), ('flag', '>i4'), ('or_mask', '>i4'), ('err', '>f4'),
                 ('sky', '>f4'), ('no', '>f4')]))
            self.model_spec = fits.data.view(dtype=np.dtype(
                [('no', '>f4'), ('wl', '>f4'), ('error', '>f4'), ('flag', '>i4'), ('or_mask', '>i4'), ('err', '>f4'),
                 ('sky', '>f4'), ('flux', '>f4')]))
        except AttributeError: # If doesn't work, read the file... 
            fits = atpy.Table(fits, hdu='COADD')
            fits.data['loglam'] = 10**fits.data['loglam']
            self.obs_spec = fits.data.view(dtype=np.dtype(
                [('flux', '>f4'), ('wl', '>f4'), ('error', '>f4'), ('flag', '>i4'), ('or_mask', '>i4'), ('err', '>f4'),
                 ('sky', '>f4'), ('no', '>f4')]))
            self.model_spec = fits.data.view(dtype=np.dtype(
                [('no', '>f4'), ('wl', '>f4'), ('error', '>f4'), ('flag', '>i4'), ('or_mask', '>i4'), ('err', '>f4'),
                 ('sky', '>f4'), ('flux', '>f4')]))
            
        
        self.obs_spec['flux'] *= 1e-17
        self.obs_spec['error'] *= 1e-17
        self.model_spec['flux'] *= 1e-17
        
        return spec2filterset(filterset, self.obs_spec, self.model_spec, badpxl_tolerance)
