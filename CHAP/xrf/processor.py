from CHAP.processor import Processor

class ElementConcentrationMapProcessor(Processor):
    """A processor that takes a fit configuration and returns map of
    element concentrations.
    """
    
    def process(self, data, pymca_fit_config_file, monitor=1e10):
        """Return map of element concentrations.
        
        :param data: A 3d array of the detector data.
        :type data: numpy.ndarray
        :param pymca_fit_config_file: The fit configuration file from 
            the XRF detector data
        :type pmyca_fit_config_file: str
        :return: A NeXus structure with element concentrations at each
            point on the map for each element.
        :rtype: nexusformat.nexus.NXroot
        """
        from PyMca5.PyMcaIO import ConfigDict
        
        config = ConfigDict.ConfigDict()
        config.read(pymca_fit_config_file)
        
        return self.spectra_to_mass_fraction_maps(config, data[0]['data'], monitor)
    
    def spectrum_to_mass_fractions(self, config, spectrum, monitor):
        """ Return a dictionary of mass fractions by element.

        :param config: Configuration object for the pymca. 
        :type config: PyMca5.PyMcaIO.ConfigDict.ConfigDict  
        :param spectrum: One spectrum of MCA data.
        :type spectrum: nexusformat.nexus.tree.NXfield
        :param monitor: defaults to 1e10
        :type monitor: float, optional
        :return: A dictionary that contains element name and the
            element concentration at one point.
        :rtype: dict
        """
        from PyMca5.PyMcaPhysics.xrf.ClassMcaTheory import McaTheory
        from PyMca5.PyMcaPhysics.xrf.ConcentrationsTool import ConcentrationsTool
    
        advanced_fit = McaTheory(config=config)
        advanced_fit.enableOptimizedLinearFit()

        if 'concentrations' in config:
            mass_fraction_tool = ConcentrationsTool(config['concentrations'])
        else:
            mass_fraction_tool = None

        advanced_fit.setData(y=spectrum)
        advanced_fit.estimate()

        if (mass_fraction_tool is not None) and (advanced_fit._fluoRates is None):
            fitresult, result = advanced_fit.startfit(digest=1)
        else:
            fitresult = advanced_fit.startfit(digest=0)
            result = advanced_fit.imagingDigestResult()

        if mass_fraction_tool is not None:
            temp = {}
            temp['fitresult'] = fitresult
            temp['result'] = result
            temp['result']['config'] = advanced_fit.config
            mass_fraction_tool.config['flux'] = monitor
            conc = mass_fraction_tool.processFitResult(
                fitresult=temp,
                elementsfrommatrix=False,
                fluorates=advanced_fit._fluoRates
                )
            return conc['mass fraction']
        else:
            pass


    def spectra_to_mass_fraction_maps(self, config, spectra_map, monitor):
        """Return a NeXus structure containing maps of element concentrations.

        :param config: Configuration file for the detector data. 
        :type config: PyMca5.PyMcaIO.ConfigDict.ConfigDict  
        :param spectra_map: A 3d array of the detector data.
        :type specta_map: numpy.ndarray
        :return: A NeXus structure with element concentrations at each
            point on the map for each element.
        :rtype: nexusformat.nexus.NXroot
        """
        from nexusformat.nexus import (NXdata, NXprocess, NXfield, NXroot, NXentry)
        import numpy as np
        from json import dumps
        
        map_shape = spectra_map.shape[0:2]

        root = NXroot(NXprocess(NXdata()))

        root['process']['data']['pymca_fit_configuration'] = NXfield()
        root['process']['data']['pymca_fit_configuration'] = dumps(config)

        for element_name,transition in config['peaks'].items():
            if isinstance(transition, list):
                for item in transition:
                    root['process']['data'][f"{element_name} {item}"] = NXfield(value = np.empty(map_shape))
            else:
                root['process']['data'][f"{element_name} {transition}"] = NXfield(value = np.empty(map_shape))

        for i, row in enumerate(spectra_map):
            for j, cell in enumerate(row):
                a = self.spectrum_to_mass_fractions(config, cell, monitor)
                for element,conc in a.items():
                    root['process']['data'][element][i,j] = conc

        return root

        
if __name__ == '__main__':
    # local modules
    from CHAP.processor import main

    main()
