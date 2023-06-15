class ElementConcentrationMapProcessor(Processor):
    """
    A processor that takes a fit configuration and returns map of element concentrations.
    """
    def process(self,data):
        """
        Returns map of element concentrations 
        """
        print data
        return data

        
if __name__ == '__main__':
    # local modules
    from CHAP.processor import main

    main()
