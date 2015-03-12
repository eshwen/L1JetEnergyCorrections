"""
Setup samples here to be used in CRAB3 configs

For each sample, we have a simple Dataset namedtuple. Fields are inputDataset
and unitsPerJob. We then store all samples in a dict.

Usage:

from samples import samples

dataset = "TTbarFall13PU20bx25"
config.General.requestName = dataset
config.Data.inputDataset = samples[dataset].inputDataset
config.Data.unitsPerJob = samples[dataset].unitsPerJob

"""

from collections import namedtuple
import re

# handly data structure to store some attributes for each dataset
Dataset = namedtuple("Dataset", "inputDataset unitsPerJob")

# This dict holds ALL samples
samples = {

    "TTbarFall13PU20bx25": Dataset(inputDataset='/TT_Tune4C_13TeV-pythia8-tauola/Fall13dr-tsg_PU20bx25_POSTLS162_V2-v1/GEN-SIM-RAW',
                                    unitsPerJob=100),

    "QCDFlatSpring14": Dataset(inputDataset='/QCD_Pt-15to3000_Tune4C_Flat_13TeV_pythia8/Spring14dr-Flat20to50_POSTLS170_V5-v1/GEN-SIM-RAW',
                                unitsPerJob=50)
}

# Add in QCD pt binned samples here easily
ptbins = [15, 30, 50, 80, 120, 170, 300, 470, 600, 800, 1000, 1400, 1800]
for i, ptmin in enumerate(ptbins[:-1]):
    ptmax = ptbins[i+1]

    # Phys14 AVEPU20 25ns
    key = "QCD_Pt-%dto%d_Phys14_AVE20BX25" % (ptmin, ptmax)
    dset = Dataset(inputDataset="/QCD_Pt-%dto%d_Tune4C_13TeV_pythia8/Phys14DR-AVE20BX25_tsg_castor_PHYS14_25_V3-v1/GEN-SIM-RAW" % (ptmin, ptmax),
                    unitsPerJob=50)
    samples[key] = dset

    # Phys14  AVEPU30 50ns
    key = "QCD_Pt-%dto%d_Phys14_AVE30BX50" % (ptmin, ptmax)
    dset = Dataset(inputDataset="/QCD_Pt-%dto%d_Tune4C_13TeV_pythia8/Phys14DR-AVE30BX50_tsg_castor_PHYS14_ST_V1-v1/GEN-SIM-RAW" % (ptmin, ptmax),
                    unitsPerJob=50)
    samples[key] = dset

    # Fall13 PU20 25ns
    key = "QCD_Pt-%dto%d_Fall13_PU20bx25" % (ptmin, ptmax)
    dest = Dataset(inputDataset="/QCD_Pt-%dto%d_Tune4C_13TeV_pythia8/Fall13dr-castor_tsg_PU20bx25_POSTLS162_V2-v1/GEN-SIM-RAW" % (ptmin, ptmax),
                    unitsPerJob=150)

    # Fall13 PU40 25ns
    key = "QCD_Pt-%dto%d_Fall13_PU40bx25" % (ptmin, ptmax)
    dest = Dataset(inputDataset="/QCD_Pt-%dto%d_Tune4C_13TeV_pythia8/Fall13dr-castor_tsg_PU40bx25_POSTLS162_V2-v1/GEN-SIM-RAW" % (ptmin, ptmax),
                    unitsPerJob=50)

    # Fall13 PU40 50ns
    key = "QCD_Pt-%dto%d_Fall13_PU40bx50" % (ptmin, ptmax)
    dest = Dataset(inputDataset="/QCD_Pt-%dto%d_Tune4C_13TeV_pythia8/Fall13dr-castor_tsg_PU40bx50_POSTLS162_V2-v1/GEN-SIM-RAW" % (ptmin, ptmax),
                    unitsPerJob=50)

# the last 1800 to inf ones
samples["QCD_Pt-1800_Phys14_AVE20BX25"] = Dataset(inputDataset="/QCD_Pt-1800_Tune4C_13TeV_pythia8/Phys14DR-AVE30BX50_tsg_castor_PHYS14_25_V3-v1/GEN-SIM-RAW",
                                                    unitsPerJob=50)
samples["QCD_Pt-1800_Phys14_AVE30BX50"] = Dataset(inputDataset="/QCD_Pt-1800_Tune4C_13TeV_pythia8/Phys14DR-AVE30BX50_tsg_castor_PHYS14_ST_V1-v1/GEN-SIM-RAW",
                                                    unitsPerJob=50)
samples["QCD_Pt-1800_Fall13_PU20bx25"] = Dataset(inputDataset="/QCD_Pt-1800_Tune4C_13TeV_pythia8/Fall13dr-castor_tsg_PU20bx25_POSTLS162_V2-v1/GEN-SIM-RAW",
                                                    unitsPerJob=150)
samples["QCD_Pt-1800_Fall13_PU40bx25"] = Dataset(inputDataset="/QCD_Pt-1800_Tune4C_13TeV_pythia8/Fall13dr-castor_tsg_PU40bx25_POSTLS162_V2-v1/GEN-SIM-RAW",
                                                    unitsPerJob=150)
samples["QCD_Pt-1800_Fall13_PU40bx50"] = Dataset(inputDataset="/QCD_Pt-1800_Tune4C_13TeV_pythia8/Fall13dr-castor_tsg_PU40bx50_POSTLS162_V2-v1/GEN-SIM-RAW",
                                                    unitsPerJob=150)

# adhoc mini samples for diff QCD sets
samples_qcd_Phys14_AVE20BX25 = dict((k, samples[k]) for k in samples.keys() if re.match(r"QCD_Pt-[\dto]*_Phys14_AVE20BX25", k))
samples_qcd_Phys14_AVE30BX50 = dict((k, samples[k]) for k in samples.keys() if re.match(r"QCD_Pt-[\dto]*_Phys14_AVE30BX50", k))
samples_qcd_Fall13_PU20bx25 = dict((k, samples[k]) for k in samples.keys() if re.match(r"QCD_Pt-[\dto]*_Fall13_PU20bx25", k))
samples_qcd_Fall13_PU40bx25 = dict((k, samples[k]) for k in samples.keys() if re.match(r"QCD_Pt-[\dto]*_Fall13_PU40bx25", k))
samples_qcd_Fall13_PU40bx50 = dict((k, samples[k]) for k in samples.keys() if re.match(r"QCD_Pt-[\dto]*_Fall13_PU40bx50", k))
