"""
Centralised way to keep track of pt & eta binning.

For future, may need to split up into GCT/Stage1 Vs Stage 2...
"""


import ROOT
import numpy as np
from itertools import tee, izip


ROOT.PyConfig.IgnoreCommandLineOptions = True


# taken from https://docs.python.org/2.7/library/itertools.html#recipes
def pairwise(iterable):
    """s -> (s0, s1), (s1, s2), (s2, s3) ...

    Example:
    >>> for eta_min, eta_max in pairwise(binning.eta_bins):
    ...     print eta_min, eta_max
    (0, 0.348)
    (0.348, 0.695)
    (0.695, 1.044)
    ...

    Parameters
    ----------
    iterable : Any iterable collection.

    Returns
    -------
    The type stored in iterable
    """
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)

############
# PT BINS
############
pt_bins = list(np.arange(14, 254, 4))
# wider binning at higher pt for low stats regions
pt_bins_wide = list(np.concatenate((np.arange(14, 50, 4),
                                    np.arange(50, 270, 20))))
pt_bins_stage2_old = list(np.arange(10, 1026, 4))
# wider binning for high pt
pt_bins_stage2 = list(np.concatenate((np.arange(10, 342, 4),
                                      np.arange(342, 1040, 20))))
# wider binning for HF
pt_bins_stage2_hf = list(np.concatenate((np.arange(10, 62, 4),
                                         np.arange(62, 1040, 20))))

# 8 GeV bins for resolution plots
pt_bins_8 = list(np.arange(14, 246, 8))
pt_bins_8.append(250)
# and wider ones for low stat bins
pt_bins_8_wide = list(np.concatenate((np.arange(14, 54, 8),
                                      np.arange(54, 242, 20))))
pt_bins_8_wide.append(250)

# pt bins for doing checkCalibration.py
# check_pt_bins = [[0, 20], [20, 40], [40, 60], [60, 80], [80, 120], [120, 200], [200, 300], [300, 500], [500, 1000]]
check_pt_bins = [[0, 20], [20, 30], [30, 40], [40, 50], [50, 60], [60, 80], [80, 100], [100, 300], [300, 500], [500, 1000]]  # for HTT studies, focussing on low pt

############
# ETA BINS
############
# select one of the following eta bin setups (eta_bins, eta_bins_all, eta_bins_label)
# the eta_bins_label is to hack onto the output file names so we can distinguish them

# # robins original version of eta info. Four (not in hf) discrete l1 eta values per bin
# eta_bins = [0.0, 0.348, 0.695, 1.044, 1.392, 1.74, 2.172, 3.0, 3.5, 4.0, 4.5, 5]
# eta_bins_all = [-5, -4.5, -4.0, -3.5, -3.0, -2.172, -1.74, -1.392, -1.044, -0.695, -0.348,
#                 0.0, 0.348, 0.695, 1.044, 1.392, 1.74, 2.172, 3.0, 3.5, 4.0, 4.5, 5]
# eta_bins_label = "_etaBinsOriginal"


# new version (version 2). Two discrete l1 eta values per bin (start off by going up in multiples of 0.175)...TODO: use the official end values...
# eta_bins = [0.000, 0.175, 0.350, 0.525, 0.700, 0.875, 1.050, 1.225, 1.400, 1.575, 1.750, 1.925, 2.100, 2.500, 3.000, 3.500, 3.900, 4.100, 4.500, 5.000]
# eta_bins_all = [-5.000, -4.500, -4.100, -3.900, -3.500, -3.000, -2.500, -2.100, -1.925, -1.750, -1.575, -1.400, -1.225, -1.050, -0.875, -0.700, -0.525, -0.350, -0.175,
#                   0.000, 0.175, 0.350, 0.525, 0.700, 0.875, 1.050, 1.225, 1.400, 1.575, 1.750, 1.925, 2.100, 2.500, 3.000, 3.500, 3.900, 4.100, 4.500, 5.000]
# eta_bins_label = "_etaBinsVersion2"


# # another new version (version 3). Initally two discrete l1 eta values per bin (for the first 14 discrete eta bins)
# # Then every individual bin until the end...DOESN'T WORK SO WELL BECAUSE IT INCLUDES SECTIONS THAT GET NO JETS
# eta_bins = [0.000, 0.174, 0.348, 0.552, 0.696, 0.870, 1.044, 1.218, 1.305, 1.392, 1.479, 1.566, 1.653, 1.740, 1.830, 1.930, 2.043, 2.172, 2.322, 2.500,
#             2.650, 2.964, 3.139, 3.314, 3.489, 3.664, 3.839, 4.013, 4.191, 4.363, 4.538, 4.716, 4.889, 5.191]
# eta_bins_all = [-5.191,-4.889,-4.716,-4.538,-4.363,-4.191,-4.013,-3.839,-3.664,-3.489,-3.314,-3.139,-2.964,-2.650,-2.500,-2.322,-2.172,-2.043,-1.930,-1.830,
#                 -1.740,-1.653,-1.566,-1.479,-1.392,-1.305,-1.218,-1.044,-0.870,-0.696,-0.552,-0.348,-0.174, 0.000, 0.174, 0.348, 0.552, 0.696, 0.870, 1.044,
#                 1.218, 1.305, 1.392, 1.479, 1.566, 1.653, 1.740, 1.830, 1.930, 2.043, 2.172, 2.322, 2.500, 2.650, 2.964, 3.139, 3.314, 3.489, 3.664, 3.839,
#                 4.013, 4.191, 4.363, 4.538, 4.716, 4.889, 5.191]
# eta_bins_label = "_etaBinsVersion3"


# # version 4. Like version 3 but does not include the sections where we don't get jets
# eta_bins = [0.000, 0.174, 0.348, 0.552, 0.696, 0.870, 1.044, 1.218, 1.305, 1.392, 1.479, 1.566, 1.653, 1.740, 1.830, 1.930, 2.043, 2.172, 2.322, 2.500,
#             2.650, 3.139, 3.314, 3.489, 3.664, 3.839, 4.013, 4.191, 4.363, 4.538]

# eta_bins_all = [-4.538,-4.363,-4.191,-4.013,-3.839,-3.664,-3.489,-3.314,-3.139,-2.650,-2.500,-2.322,-2.172,-2.043,-1.930,-1.830,-1.740,-1.653,-1.566,-1.479,
#                 -1.392,-1.305,-1.218,-1.044,-0.870,-0.696,-0.552,-0.348,-0.174, 0.000, 0.174, 0.348, 0.552, 0.696, 0.870, 1.044, 1.218, 1.305, 1.392, 1.479,
#                 1.566, 1.653, 1.740, 1.830, 1.930, 2.043, 2.172, 2.322, 2.500, 2.650, 3.139, 3.314, 3.489, 3.664, 3.839, 4.013, 4.191, 4.363, 4.538]
# eta_bins_label = "_etaBinsVersion4"


# eta bins for all TT (after v70.0 emulator so includes partial jets and TT30)
# eta_bins = [0.000, 0.087, 0.174, 0.261, 0.348, 0.435, 0.522, 0.609, 0.696, 0.783, 0.870, 0.957, 1.044, 1.131, 1.218, 1.305, 1.392, 1.479, 1.566, 1.653, 1.740,
#             1.830, 1.930, 2.043, 2.172, 2.322, 2.500, 2.650, 2.964, 3.139, 3.314, 3.489, 3.664, 3.839, 4.013, 4.191, 4.363, 4.538, 4.716, 4.889, 5.191]

# eta_bins_all = [-5.191,-4.889,-4.716,-4.538,-4.363,-4.191,-4.013,-3.839,-3.664,-3.489,-3.314,-3.139,-2.964,-2.650,-2.500,-2.322,-2.172,-2.043,-1.930,-1.830,-1.740,
#                 -1.653,-1.566,-1.479,-1.392,-1.305,-1.218,-1.131,-1.044,-0.957,-0.870,-0.783,-0.696,-0.609,-0.522,-0.435,-0.348,-0.261,-0.174,-0.087,
#                 0.000,  0.087, 0.174, 0.261, 0.348, 0.435, 0.522, 0.609, 0.696, 0.783, 0.870, 0.957, 1.044, 1.131, 1.218, 1.305, 1.392, 1.479, 1.566, 1.653, 1.740,
#                 1.830, 1.930, 2.043, 2.172, 2.322, 2.500, 2.650, 2.964, 3.139, 3.314, 3.489, 3.664, 3.839, 4.013, 4.191, 4.363, 4.538, 4.716, 4.889, 5.191]

# eta_bins_label = "_etaBinsAllTT"


# eta bins for the selected 16
eta_bins = [0.000, 0.435, 0.783, 1.131, 1.305, 1.479, 1.653, 1.830, 1.930,
            2.043, 2.172, 2.322, 2.500, 2.964, 3.489, 4.191, 5.191] 

eta_bins_all = [-5.191, -4.191, -3.489, -2.964, -2.500, -2.322, -2.172, -2.043,
                -1.930, -1.830, -1.653, -1.479, -1.305, -1.131, -0.783, -0.435,
                0.000, 0.435, 0.783, 1.131, 1.305, 1.479, 1.653, 1.830, 1.930,
                2.043, 2.172, 2.322, 2.500, 2.964, 3.489, 4.191, 5.191] 

eta_bins_label = "_etaBinsSel16"
# KEY (TT:ETA) chunks==bin
# 01: 0_0.087
# 02: 0.087_0.174
# 03: 0.174_0.261
# 04: 0.261_0.348
# 05: 0.348_0.435

# 06: 0.435_0.522
# 07: 0.522_0.609
# 08: 0.609_0.696
# 09: 0.696_0.783

# 10: 0.783_0.87
# 11: 0.87_0.957
# 12: 0.957_1.044
# 13: 1.044_1.131

# 14: 1.131_1.218
# 15: 1.218_1.305

# 16: 1.305_1.392
# 17: 1.392_1.479

# 18: 1.479_1.566
# 19: 1.566_1.653

# 20: 1.653_1.74
# 21: 1.74_1.83

# 22: 1.83_1.93

# 23: 1.93_2.043

# 24: 2.043_2.172

# 25: 2.172_2.322

# 26: 2.322_2.5

# 27: 2.5_2.65
# 28: 2.65_2.964

# 30: 2.964_3.139
# 31: 3.139_3.314
# 32: 3.314_3.489

# 33: 3.489_3.664
# 34: 3.664_3.839
# 35: 3.839_4.013
# 36: 4.013_4.191

# 37: 4.191_4.363
# 38: 4.363_4.538
# 39: 4.538_4.716
# 40: 4.716_4.889
# 41: 4.889_5.191



eta_bins_central = [eta for eta in eta_bins if eta < 3.1]
eta_bins_forward = [eta for eta in eta_bins if eta > 2.9]
# a handy palette of colours. TODO: add more colours as we now have more bins
# eta_bin_colors = [ROOT.kRed,
#                   ROOT.kBlue,
#                   ROOT.kGreen + 2,
#                   ROOT.kBlack,
#                   ROOT.kMagenta,
#                   ROOT.kOrange + 7,
#                   ROOT.kAzure + 1,
#                   ROOT.kRed + 3,
#                   ROOT.kViolet + 1,
#                   ROOT.kOrange,
#                   ROOT.kTeal - 5
#                   ]

# for sel 16 eta binning
eta_bin_colors = [
                  ROOT.kBlue+2,
                  ROOT.kBlue,
                  ROOT.kCyan+1,
                  ROOT.kGreen+2,
                  ROOT.kGreen,  
                  ROOT.kYellow+2,
                  ROOT.kOrange,
                  ROOT.kOrange+7,
                  ROOT.kRed+2,  
                  ROOT.kRed,
                  ROOT.kMagenta+3,
                  ROOT.kMagenta,
                  ROOT.kBlue+2,
                  ROOT.kCyan+1,
                  ROOT.kGreen+2,
                  ROOT.kGreen,
                  ]


##########
# PU BINS
##########
# pu_bins = [[25, 35], [40, 50], [55, 65]]
pu_bins = [[40, 50], [50, 60]]
#pu_bins = [[50, 60]] # just to do one bin by itself

pu_bins_lower = [[0, 5], [8, 12], [15, 25]] # run260627 lower PU overall - mean 10
