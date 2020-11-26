# @LogService log

"""
File: my_fijipyscript.py
Author: Sebastian Rhode
Date: 2020_11_25
Version: 0.7

The idea of this module is to provide a template showing some of the required
code parts in order to create modules based on Fiji. The chosen processing step
is just an example for your image analysis pipeline

Disclaimer: Use at your own risk!

"""

# required import
import os
import json
from java.lang import Double, Integer
from ij import IJ, ImagePlus, ImageStack, Prefs
from ij.process import ImageProcessor, LUT
from ij.plugin.filter import RankFilters
from loci.plugins import BF
from loci.plugins.in import ImporterOptions
from loci.plugins import LociExporter
from loci.plugins.out import Exporter
from ij.io import FileSaver
from org.scijava.log import LogLevel
import time

# helper function to apply the filter
def apply_filter(imp,
                 radius=5,
                 filtertype='MEDIAN'):

    # initialize filter
    filter = RankFilters()

    # create filter dictionary
    filterdict = {}
    filterdict['MEAN'] = RankFilters.MEAN
    filterdict['MIN'] = RankFilters.MIN
    filterdict['MAX'] = RankFilters.MAX
    filterdict['MEDIAN'] = RankFilters.MEDIAN
    filterdict['VARIANCE'] = RankFilters.VARIANCE
    filterdict['OPEN'] = RankFilters.OPEN
    filterdict['DESPECKLE'] = RankFilters.DESPECKLE

    # get the stack and number of slices
    stack = imp.getStack()  # get the stack within the ImagePlus
    nslices = stack.getSize()  # get the number of slices

    # apply filter based on filtertype
    if filtertype in filterdict:
        for index in range(1, nslices + 1):
            ip = stack.getProcessor(index)
            filter.rank(ip, radius, filterdict[filtertype])
    else:
        print("Argument 'filtertype': {filtertype} not found")

    return imp


############################################################################


def run(imagefile, useBF=True, series=0):

    log.log(LogLevel.INFO, 'Image Filename : ' + imagefile)

    if not useBF:
        # using IJ static method
        imp = IJ.openImage(imagefile)

    if useBF:

        # initialize the importer options
        options = ImporterOptions()
        options.setOpenAllSeries(True)
        options.setShowOMEXML(False)
        options.setConcatenate(True)
        options.setAutoscale(True)
        options.setId(imagefile)

        # open the ImgPlus
        imps = BF.openImagePlus(options)
        imp = imps[series]

    # apply the filter
    if FILTERTYPE != 'NONE':

        # apply filter
        log.log(LogLevel.INFO, 'Apply Filter  : ' + FILTERTYPE)
        log.log(LogLevel.INFO, 'Filter Radius : ' + str(FILTER_RADIUS))

        # apply the filter based on the chosen type
        imp = apply_filter(imp,
                           radius=FILTER_RADIUS,
                           filtertype=FILTERTYPE)

    if FILTERTYPE == 'NONE':
        log.log(LogLevel.INFO, 'No filter selected. Do nothing.')

    return imp


#########################################################################

# Parse Inputs of Module
INPUT_JSON = json.loads(os.environ['WFE_INPUT_JSON'])
IMAGEPATH = INPUT_JSON['IMAGEPATH']

# suffix for the filename of the saved data
SUFFIX_FL = '_FILTERED'

# parameters for filter
FILTERTYPE = INPUT_JSON['FILTERTYPE']
FILTER_RADIUS = int(INPUT_JSON['FILTER_RADIUS'])
SAVEFORMAT = 'ome.tiff'

log.log(LogLevel.INFO, 'Starting ...')
log.log(LogLevel.INFO, 'Filename               : ' + IMAGEPATH)
log.log(LogLevel.INFO, 'Save Format used       : ' + SAVEFORMAT)
log.log(LogLevel.INFO, '------------  START IMAGE ANALYSIS ------------')

##############################################################

# define path for the output
outputimagepath = '/output/' + os.path.basename(IMAGEPATH)
basename = os.path.splitext(outputimagepath)[0]

# remove the extra .ome before reassembling the filename
if basename[-4:] == '.ome':
    basename = basename[:-4]
    log.log(LogLevel.INFO, 'New basename for output :' + basename)

# save processed image
outputimagepath = basename + SUFFIX_FL + '.' + SAVEFORMAT

#############   RUN MAIN IMAGE ANALYSIS PIPELINE ##########

# get the starting time of processing pipeline
start = time.clock()

# run image analysis pipeline
filtered_image = run(IMAGEPATH,
                     useBF=True,
                     series=0)

# get time at the end and calc duration of processing
end = time.clock()
log.log(LogLevel.INFO, 'Duration of whole Processing : ' + str(end - start))

###########################################################

start = time.clock()

# create the argument string for the BioFormats Exporter and save as OME.TIFF
paramstring = "outfile=" + outputimagepath + " " + "windowless=true compression=Uncompressed saveROI=false"
plugin = LociExporter()
plugin.arg = paramstring
exporter = Exporter(plugin, filtered_image)
exporter.run()

# get time at the end and calc duration of processing
end = time.clock()
log.log(LogLevel.INFO, 'Duration of saving as OME.TIFF : ' + str(end - start))

# write output JSON
log.log(LogLevel.INFO, 'Writing output JSON file ...')
output_json = {"FILTERED_IMAGE": outputimagepath}

with open("/output/" + INPUT_JSON['WFE_output_params_file'], 'w') as f:
    json.dump(output_json, f)

# finish
log.log(LogLevel.INFO, 'Done.')

# exit
os._exit()
