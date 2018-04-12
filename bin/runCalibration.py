#!/usr/bin/env python
"""
This script takes as input the output file from RunMatcher, and loops over
matched genjet/L1 jet pairs, plotting interesting things and producing a
correction function for each eta bin. By default it goes over all eta bins.

It can also re-fit the correction curve to an existing graph, saving time.
In this case, use the --redo_correction_fit option, and the input file is
the output from a previous running of this script.

Usage: see
python runCalibration.py -h

Originally by Nick Wardle, modified(hacked to shreds) by Robin Aggleton
"""

import ROOT
import os
import sys
import numpy as np
import argparse
import binning
from binning import pairwise
import common_utils as cu
from math import sqrt, log


ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gStyle.SetOptStat(0)
ROOT.gROOT.SetBatch(1)
ROOT.gStyle.SetOptFit(1111)
ROOT.TH1.SetDefaultSumw2(True)


# definition of the response function to fit to get our correction function
# MAKE SURE IT'S THE SAME ONE THAT IS USED IN THE EMULATOR
central_fit_conventional = ROOT.TF1("fitfcn", "[0]+[1]/(pow(log10(x),2)+[2])+[3]*exp(-[4]*(log10(x)-[5])*(log10(x)-[5]))")
central_fit_JetMet1 = ROOT.TF1("fitfcn", "[0]+[1]/(pow(log10(x),2)+[2])+[3]*exp(-([4]*(log10(x)-[5])*(log10(x)-[5])))+[6]*exp(-([7]*(log10(x)-[8])*(log10(x)-[8])))")
central_fit_JetMetErr = ROOT.TF1("fitfcn", "[0]+[1]*TMath::Erf([2]*(log10(x)-[3])+[4]*exp([5]*(log10(x)-[6])*(log10(x)-[6])))")

forward_fit = ROOT.TF1("fitfcn", "pol0")

# Burr Type 3 distribution for response hist fitting
# [0] is c in scipy notation
# [1] is d in scipy notation
# [2] is an overall normalisation factor
# [3] is a location factor
# [4] is a scale factor
burr3_fit = ROOT.TF1("burr3", "[2]*[0]*[1]*pow((x-[3])/[4], -1.-[0]) / pow(1+pow((x-[3])/[4], -[0]), 1+[1] )", 0, 2)

def setup_burr3():
    burr3_fit.SetParameter(0, 3.64850e+00)
    burr3_fit.SetParameter(1, 7.06077e-01)
    burr3_fit.SetParameter(2, 1.28317e+04)
    burr3_fit.SetParameter(3, -1.50503e-02)
    burr3_fit.SetParameter(4, 4.87032e-01)

def setup_burr3_higherEta():
    burr3_fit.SetParameter(0, 4.08877e+00)
    burr3_fit.SetParameter(1, 1.40812e+00)
    burr3_fit.SetParameter(2, 9.49084e+01)
    burr3_fit.SetParameter(3, -2.06920e-01)
    burr3_fit.SetParameter(4, 9.41943e-01)

setup_burr3()

# Burr Type 12 distribution for response hist fitting
# [0] is c in wiki notation
# [1] is k in wiki notation
# [2] is an overall normalisation factor
# [3] is a location factor
# [4] is a scale factor
burr12_fit = ROOT.TF1("burr12", "[2]*[0]*[1]*pow((x-[3])/[4], [0]-1.) / pow(1+pow((x-[3])/[4], [0]), 1+[1] )", 0, 2)
burr12_fit.SetParameter(0, 2.96)
burr12_fit.SetParameter(1, 1.31)
burr12_fit.SetParameter(2, 367)
burr12_fit.SetParameter(3, 0)
burr12_fit.SetParameter(4, 1.01)

# Curve Fit defaults
GCT_DEFAULT_PARAMS = [1, 5, 1, -25, 0.01, -20]
STAGE1_DEFAULT_PARAMS = [1, 5, 1, -25, 0.01, -20]
# STAGE2_DEFAULT_PARAMS_ORIGINAL = [-0.5, 50, 1, -80, 0.01, -20]
STAGE2_DEFAULT_PARAMS_CONVENTIONAL = [6.89, -252.79, 27.01, 4345.01, 0.01, -20.9794]
STAGE2_DEFAULT_PARAMS_JETMET1 = [-11.64, -43.50, 1.19, 2190.7, 0, -19.51, -18.7426, 0.22, 0.98] # new jet met function has three more parameters
#STAGE2_DEFAULT_PARAMS_JETMETERR = [1.4036, -1398000, 0, 0.2249, 0, -2.926, 1.175] # other new jet met function, err func style (no idea what params should be)
STAGE2_DEFAULT_PARAMS_JETMETERR = [1.86431, -1.34016e+06, -2.85506e-08, 20.2633, -6.40935e-07, -1.54, 1.06511]

#######################################################
# select which fit function and input parameters to use
#######################################################
# central_fit_select = central_fit_conventional
# STAGE2_DEFAULT_PARAMS_SELECT = STAGE2_DEFAULT_PARAMS_CONVENTIONAL

# central_fit_select = central_fit_JetMet1
# STAGE2_DEFAULT_PARAMS_SELECT = STAGE2_DEFAULT_PARAMS_JETMET1

central_fit_select = central_fit_JetMetErr
STAGE2_DEFAULT_PARAMS_SELECT = STAGE2_DEFAULT_PARAMS_JETMETERR


def set_fit_params(fitfunc, params):
    """Set function parameters.

    Parameters
    ----------
    fitfunc : TF1
        Or anything with a SetParameter() method.
    params : list, iterable
        List of parameter values, must be in same order as parameter index.
    """
    for ind, val in enumerate(params):
        fitfunc.SetParameter(ind, val)


def generate_eta_graph_name(absetamin, absetamax):
    """
    Function to generate graph name for given eta bin,
    so co-ordinated between functions/modules.
    """
    return "l1corr_eta_%g_%g" % (absetamin, absetamax)


def get_hist_bin_contents(hist):
    return np.array([hist.GetBinContent(i) for i in range(1, hist.GetNbinsX() + 1)])


def do_gauss_response_hist_fit(hrsp):
    """Fit Gaussian function to response histogram."""
    # but only if we have a sensible number of entries
    fitStatus = -1
    mean = -999
    err = -999
    if hrsp.GetEntries() >= 3:
        # Try the fit mutliple times, beacuse it can converge on the 2nd or 3rd
        # iteration but not on the 1st...
        fit_counter = 3
        while fitStatus != 0 and fit_counter > 0:
            fitStatus = int(hrsp.Fit("gaus", "QER", "",
                                     hrsp.GetMean() - 1. * hrsp.GetRMS(),
                                     hrsp.GetMean() + 1. * hrsp.GetRMS()))
            # fitStatus = int(hrsp.Fit("burr", "QER", "", 0, 2))
            fit_counter -= 1
            if fitStatus == 0:
                mean = hrsp.GetFunction("gaus").GetParameter(1)
                err = hrsp.GetFunction("gaus").GetParError(1)
                # mean = hrsp.GetFunction("burr").GetMaximumX()
                # err = hrsp.GetMeanError()
                break

    # check if we have a bad fit - either fit status != 0, or
    # fit mean is not close to raw mean. in either case use raw mean
    if fitStatus != 0:  # or (xlow > 50 and abs((mean / hrsp.GetMean()) - 1) > 0.2):
        print "Poor Fit: fit mean:", mean, "raw mean:", hrsp.GetMean(), "fit status:", fitStatus
        mean = hrsp.GetMean()
        err = hrsp.GetMeanError()
    return mean, err


def calc_burr_mode_error(mode, c, err_c, d, err_d, s, err_s, mu, err_mu):
    """Calculate the total error on the mode from errors on fitted params.

    c, d are shape params
    s is scale param
    mu is location param
    """
    total = ((burr_diff_mu() * err_mu)**2 + (burr_diff_s(c, d) * err_s)**2 +
             (burr_diff_c(mode, c, d, s, mu) * err_c)**2 + (burr_diff_d(c, d, s) * err_d)**2)
    return sqrt(total)


def burr_diff_mu():
    """Partial differential of Burr3 mode wrt mu"""
    return 1.


def burr_diff_s(c, d):
    """Partial differential of Burr3 mode wrt s"""
    comp = (c * d + 1.) / (c + 1.)
    if comp > 0:
        return comp**(1. / c)
    else:
        return 0


def burr_diff_c(mode, c, d, s, mu):
    """Partial differential of Burr3 mode wrt c"""
    part1 = 0 # if s <=0 else log(s) * (-1. / (c**2))
    comp = (c + 1.) / (c * d - 1.)
    part2 = 0 if comp <= 0 else log(comp) * (1. / c**2)
    part3 = (d + 1) / (c * (c * d - 1.) * (c + 1.))
    return (mode-mu) * (part1 + part2 + part3)


def burr_diff_d(c, d, s):
    """Partial differential of Burr3 mode wrt d"""
    comp = (c * d - 1.) / (1. + c)
    if comp > 0:
        return (s / (c * d - 1.)) * (comp)**(1. / c)
    else:
        return 0


def do_burr_response_hist_fit(hrsp, setup_fn):
    """Fit Burr function to response histogram."""
    # but only if we have a sensible number of entries
    fitStatus = -1
    mode = -999
    err = -999
    if hrsp.GetEntries() >= 10:
        # Try the fit mutliple times, beacuse it can converge on the 2nd or 3rd
        # iteration but not on the 1st...
        # fit_counter = 3
        # while fitStatus != 0 and fit_counter > 0:
        #     print 'Iterations left', fit_counter
        #     fitStatus = int(hrsp.Fit("burr3", "QE"))
        #     fit_counter -= 1
        #     if fitStatus == 0 and hrsp.GetFunction("burr3").GetMaximumX() > 0:
        #         mode = hrsp.GetFunction("burr3").GetMaximumX()
        #         err = hrsp.GetMeanError()
        #         break
        # Ok, so it didn't work, so let's rebin with double bin width and retry
        print 'Doubling bin size'
        hrsp.Rebin(2)
        fit_counter = 3
        setup_fn()
        while fitStatus != 0 and fit_counter > 0:
            print 'Iterations left', fit_counter
            fitStatus = int(hrsp.Fit("burr3", "QE"))
            fit_counter -= 1
            if fitStatus == 0 and hrsp.GetFunction("burr3").GetMaximumX() > 0:
                burr_fn = hrsp.GetFunction("burr3")
                mode = burr_fn.GetMaximumX()
                c = burr_fn.GetParameter(0)
                err_c = burr_fn.GetParError(0)
                d = burr_fn.GetParameter(1)
                err_d = burr_fn.GetParError(1)
                mu = burr_fn.GetParameter(3)
                err_mu = burr_fn.GetParError(3)
                s = burr_fn.GetParameter(4)
                err_s = burr_fn.GetParError(4)
                err = calc_burr_mode_error(mode, c, err_c, d, err_d, s, err_s, mu, err_mu)
                break

    # check if we have a bad fit - either fit status != 0, or
    # fit mode is not close to raw mode. in either case use raw mode
    # or (xlow > 50 and abs((mode / hrsp.GetMean()) - 1) > 0.2):
    if (fitStatus != 0 or mode <= 0 or err <= 0 or
        (hrsp.GetFunction("burr3").GetMaximum() / hrsp.GetMaximum()) < 0.8 or
        (hrsp.GetFunction("burr3").GetMaximum() / hrsp.GetMaximum()) > 1.2 ):
        print "Poor Fit: fit mode:", mode, "raw mean:", hrsp.GetMean(), "fit status:", fitStatus
        mode = hrsp.GetMean()
        err = hrsp.GetMeanError()
    return mode, err


def make_correction_curves(inputfile, outputfile, ptBins_in, absetamin, absetamax,
                           fitfcn, do_genjet_plots, do_correction_fit,
                           pu_min, pu_max, do_burr):
    """
    Do all the relevant hists and fitting, for one eta bin.

    Briefly: make plots of L1 jet pT, and response (= l1/gen) for each genjet pt bin.
    Then find the mean L1 jet pT for the pt bin.
    Then fit a Gaussian to each response histogram, and get the mean.
    Plot 1/fitted mean Vs mean L1 pT.
    Then fit with given function, and return parameters.
    All of these plots are stored in the TFile, outputfile.

    Returns parameters of succeful fit.

    inputfile: TFile. Must contain TTree named "valid", full of pair quantities.

    outputfile: TFile. To store output histograms.

    ptBins_in: list. Edges of pt bins used to divide up correction curve.

    absetamin: float. Lower edge of eta bin, must be >= 0.

    absetamax: float. Upper edge of eta bin, must be > 0.

    fitfcn: TF1. Function to fit for correction curve.

    do_genjet_plots: bool. Whether to make plots for reference jets. Not used
        in calcualtion of correction curve, but handy for debugging.

    do_correction_fit: bool. Whether to actually fit the correction curve.

    pu_min: float. Cut on minimum number of PU vertices.

    pu_max: float. Cut on maximum number of PU vertices.

    do_burr: bool. If True, use Burr fn to fit response histograms.
    The default is to use a Gaussian.
    """

    print "Doing PU range: %g - %g" % (pu_min, pu_max)
    print "Running over pT bins:", ptBins_in

    # Input tree
    tree_raw = cu.get_from_file(inputfile, "valid")

    # Output folders
    output_f = outputfile.mkdir('eta_%g_%g' % (absetamin, absetamax))
    output_f_hists = output_f.mkdir("Histograms")

    # Eta cut string
    eta_cut = ROOT.TCut("TMath::Abs(eta)<%g && TMath::Abs(eta) > %g" % (absetamax, absetamin))

    # PU cut string
    if hasattr(tree_raw, "numPUVertices"):
        pu_cut = ROOT.TCut("numPUVertices >= %g && numPUVertices <= %g" % (pu_min, pu_max))
    else:
        pu_cut = ROOT.TCut("")

    # Avoid L1 saturated jets cut (from 2017 any l1 jet with a saturated tower is auto given pt=1024GeV)
    avoidSaturation_cut = ROOT.TCut("pt < 1023.1")

    # Total cut
    total_cut = ROOT.TCut(eta_cut)
    total_cut += pu_cut  # need to use += and not && cos TCut all fubar
    total_cut += avoidSaturation_cut
    print total_cut

    # Draw response (pT^L1/pT^Gen) for all pt bins
    tree_raw.Draw("rsp>>hrsp_eta_%g_%g(50,0,2)" % (absetamin, absetamax), total_cut, "goff")
    hrsp_eta = ROOT.gROOT.FindObject("hrsp_eta_%g_%g" % (absetamin, absetamax))
    hrsp_eta.SetTitle(";response (p_{T}^{L1}/p_{T}^{Ref});")
    output_f_hists.WriteTObject(hrsp_eta)

    nb, pt_min, pt_max = 2048, 0, 1024

    # Draw rsp (pT^L1/pT^Gen) Vs GenJet pT
    tree_raw.Draw("rsp:ptRef>>h2d_rsp_gen(%d,%g,%g,150,0,5)" % (nb, pt_min, pt_max), total_cut, "goff")
    h2d_rsp_gen = ROOT.gROOT.FindObject("h2d_rsp_gen")
    h2d_rsp_gen.SetTitle(";p_{T}^{Ref} [GeV];response (p_{T}^{L1}/p_{T}^{Ref})")
    output_f_hists.WriteTObject(h2d_rsp_gen)

    # Draw rsp (pT^L1/pT^Gen) Vs L1 pT
    tree_raw.Draw("rsp:pt>>h2d_rsp_l1(%d,%g,%g,150,0,5)" % (nb, pt_min, pt_max), total_cut, "goff")
    h2d_rsp_l1 = ROOT.gROOT.FindObject("h2d_rsp_l1")
    h2d_rsp_l1.SetTitle(";p_{T}^{L1} [GeV];response (p_{T}^{L1}/p_{T}^{Ref})")
    output_f_hists.WriteTObject(h2d_rsp_l1)

    # draw pT^L1 Vs pT^Gen
    tree_raw.Draw("pt:ptRef>>h2d_gen_l1(%d,%g,%g,%d,%g,%g)" % (nb, pt_min, pt_max, nb, pt_min, pt_max), total_cut, "goff")
    h2d_gen_l1 = ROOT.gROOT.FindObject("h2d_gen_l1")
    h2d_gen_l1.SetTitle(";p_{T}^{Ref} [GeV];p_{T}^{L1} [GeV]")
    output_f_hists.WriteTObject(h2d_gen_l1)

    # Go through and find histogram bin edges that are closest to the input pt
    # bin edges, and store for future use
    ptBins = []
    bin_indices = []
    for i, ptR in enumerate(ptBins_in[0:-1]):
        bin1 = h2d_rsp_gen.GetXaxis().FindBin(ptR)
        bin2 = h2d_rsp_gen.GetXaxis().FindBin(ptBins_in[i + 1]) - 1
        xlow = h2d_rsp_gen.GetXaxis().GetBinLowEdge(bin1)
        xup = h2d_rsp_gen.GetXaxis().GetBinLowEdge(bin2 + 1)
        bin_indices.append([bin1, bin2])
        ptBins.append(xlow)
    ptBins.append(xup)  # only need this last one

    gr = ROOT.TGraphErrors()  # 1/<rsp> VS ptL1
    gr_gen = ROOT.TGraphErrors()  # 1/<rsp> VS ptGen
    grc = 0

    # Iterate over pT^Gen bins, and for each:
    # - Project 2D hist so we have a plot of response for given pT^Gen range
    # - Fit a Gaussian (if possible) to this resp histogram to get <response>
    # - Plot the L1 pT for given pT^Gen range (remember, for matched pairs)
    # - Get average response, <pT^L1>, from 1D L1 pT hist
    # - Add a new graph point, x=<pT^L1> y=<response> for this pT^Gen bin
    for i, ptR in enumerate(ptBins[0:-1]):

        bin1 = bin_indices[i][0]
        bin2 = bin_indices[i][1]
        # h2d_calib.GetXaxis().FindBin(ptR)
        # h2d_calib.GetXaxis().FindBin(ptBins[i+1])-1
        # print "Binning mis-matches", ptR, ptBins[i+1],
        # h2d_calib.GetXaxis().GetBinLowEdge(bin1),h2d_calib.GetXaxis().GetBinLowEdge(bin2+1)

        xlow = ptR
        xhigh = ptBins[i + 1]

        # Plot of response for given pT Gen bin
        hrsp = h2d_rsp_gen.ProjectionY("Rsp_genpt_%g_%g" % (xlow, xhigh), bin1, bin2)

        # cut on ref jet pt
        pt_cut = ROOT.TCut("ptRef < %g && ptRef > %g " % (xhigh, xlow))
        total_cut = ROOT.TCut(eta_cut)
        total_cut += pu_cut
        total_cut += avoidSaturation_cut
        total_cut += pt_cut
        print total_cut

        # Plots of pT L1 for given pT Gen bin
        tree_raw.Draw("pt>>hpt(4000, 0, 2000)", total_cut, "goff")
        hpt = ROOT.gROOT.FindObject("hpt")
        hpt.SetName("L1_pt_genpt_%g_%g" % (xlow, xhigh))
        # hpt = h2d_gen_l1.ProjectionX("L1_pt_genpt_%g_%g" % (xlow, xhigh))

        if hrsp.GetEntries() <= 0 or hpt.GetEntries() <= 0:
            print "Skipping as 0 entries"
            continue

        output_f_hists.WriteTObject(hpt)

        # Plots of pT Gen for given pT Gen bin
        if do_genjet_plots:
            tree_raw.Draw("ptRef>>hpt_gen(200)", total_cut, "goff")
            hpt_gen = ROOT.gROOT.FindObject("hpt_gen")
            hpt_gen.SetName("gen_pt_genpt_%g_%g" % (xlow, xhigh))
            output_f_hists.WriteTObject(hpt_gen)

        # Fit to resposne hist to get mean response & error on mean
        if do_burr:
            if (absetamin > 2 and i == 0):
                setup_burr3_higherEta()
            setup_fn = setup_burr3 if absetamin < 2 else setup_burr3_higherEta
            mean, err = do_burr_response_hist_fit(hrsp, setup_fn)
        else:
            mean, err = do_gauss_response_hist_fit(hrsp)

        output_f_hists.WriteTObject(hrsp)

        print "pT Gen: ", ptR, "-", ptBins[i + 1], "<pT L1>:", hpt.GetMean(), \
              "<pT Gen>:", (hpt_gen.GetMean() if do_genjet_plots else "NA"), "<rsp>:", mean

        # Since we're plotting 1/rsp on y axis, so need jacobian
        err = err / (mean**2)

        # add point to response graph vs pt
        # store if new max/min, but only max if pt > pt of previous point
        # max_pt = max(hpt.GetMean(), max_pt) if grc > 0 and hpt.GetMean() > gr.GetX()[grc-1] else max_pt
        # min_pt = min(hpt.GetMean(), min_pt)
        gr.SetPoint(grc, hpt.GetMean(), 1. / mean)
        gr.SetPointError(grc, hpt.GetMeanError(), err)
        if do_genjet_plots:
            gr_gen.SetPoint(grc, hpt_gen.GetMean(), 1. / mean)
            # gr_gen.SetPointError(grc, hpt.GetMeanError(), err)
        grc += 1

    # Label response VS pT graphs
    graph_name = generate_eta_graph_name(absetamin, absetamax)
    gr.SetName(graph_name)
    gr.GetXaxis().SetTitle("<p_{T}^{L1}> [GeV]")
    gr.GetYaxis().SetTitle("1/<p_{T}^{L1}/p_{T}^{Ref}>")

    if do_genjet_plots:
        gr_gen.SetName('gencorr_eta_%g_%g' % (absetamin, absetamax))
        gr_gen.GetXaxis().SetTitle("<p_{T}^{Ref}> [GeV]")
        gr_gen.GetYaxis().SetTitle("1/<p_{T}^{L1}/p_{T}^{Ref}>")

    # Save these graphs to file
    outputfile.WriteTObject(gr)
    if do_genjet_plots:
        outputfile.WriteTObject(gr_gen)

    # Fit correction function to response vs pT graph, add params list
    fit_params = []

    if do_correction_fit:
        sub_graph, this_fit = setup_fit(gr, fitfcn, absetamin, absetamax, outputfile)
        fit_graph, fit_params = fit_correction(sub_graph, this_fit)
        outputfile.WriteTObject(this_fit)  # function by itself
        outputfile.WriteTObject(fit_graph)  # has the function stored in it as well

    return fit_params


def setup_fit(graph, function, absetamin, absetamax, outputfile):
    """Setup for fitting (auto-calculate sensible range).

    Returns a sub-graph of only sensible points (chop off turnover at low pT,
    and any high pT tail), along with a corresponding fit function
    whose range has been set to match the sub graph.
    """
    print 'Setting up fit'
    xarr, yarr = cu.get_xy(graph)
    exarr, eyarr = cu.get_exey(graph)
    # first test out graph isn't empty
    if len(xarr) == 0:
        raise RuntimeError("graph in setup_fit() is empty")

    fit_max = max(xarr)  # Maxmimum pt for upper bound of fit

    # fit_min = 10 if absetamin > 2.9 else 10
    fit_min = min(xarr) # Minimum pt for lower bound of fit

    # For lower bound of fit, use either fit_min or the pt
    # of the maximum correction value, whichever has the larger pT.
    # Check to make sure it's not the last point on the graph
    # (e.g. if no turnover), in which case just use the default fit_min
    # Then find the index of the closest corresponding value in xarr (since
    # fit_min could correspond to a pT that isn't in the list of x-points)
    # Note that we want the maximum in the first half of the graph to avoid
    # the 'flick' at high pT in HF
    # JOE EDIT: (un)comment the next 4 lines to (not) have the flick
    max_corr = max(yarr[:len(yarr) / 2])
    max_corr_ind = yarr.index(max_corr)
    max_corr_pt = xarr[max_corr_ind]
    fit_min = max(fit_min, max_corr_pt) if (max_corr_pt != xarr[-1]) and (max_corr_pt != xarr[-1]) else fit_min
    min_ind = next(i for i, x in enumerate(xarr) if x >= fit_min)

    # To find upper limit of fit, we need to detect if & where there is a turnover
    # (i.e. where the gradient goes from -ve to +ve)
    # This is made difficult by the fact the graph may be 'noisy' and simply
    # taking the gradient may not be enough (and give multiple points where
    # the gradient changes). To counter this, we smooth the gradient by
    # averaging over several points
    def moving_average(arr, n):
        """Returns a np.array of moving-averages of array arr, where each
        point in the rerurned array is the average of the consecutive n points
        in the original array.

        By definition, this will return an array of length len(arr) + 1 - n
        """
        return np.array([np.mean(arr[i:i+n]) for i in range(0, len(arr) - n + 1)])

    def calc_crossing(arr):
        """Calculate value at which value the array crosses 0.

        Looks at points in groups of 4, and finds the smallest group
        where the first 2 points < 0, and the next 2 points > 0.

        This ignores values which peak above 0 for 1 point.

        Returns the array (index, value) of the point closest to 0.
        """
        for i in range(2, len(arr)):
            group = np.concatenate((-1 * arr[i-2: i], arr[i: i+2]))
            if np.all(group > 0):
                return i - 2 + list(group).index(np.min(group)), np.min(group)
        return None, None

    grad = np.gradient(yarr, 1)
    n_sample = 5
    intercept_ind, intercept = None, None
    # keep incrementing the smooting value until we get a clean intercept
    while not intercept_ind and not intercept:
        x_ave = moving_average(xarr, n_sample)
        grad_ave = moving_average(grad, n_sample)
        intercept_ind, intercept = calc_crossing(grad_ave)
        n_sample += 1
        # quit if we've got stuck
        if n_sample == 12:
            break

    if intercept and intercept_ind:
        print 'Found minima'
        print 'Smoothing param:', n_sample
        # find closest x value to intercept
        max_ind, fit_max = closest_element(xarr, x_ave[intercept_ind])
    else:
        print '! Could not find minima, falling back to just using min()'
        # Here we assume a failure to find any minima, so fallback and use
        # the smallest point.
        max_ind = list(yarr).index(min(yarr))
        fit_max = xarr[max_ind]

    #############
    # JOE_HACKs #
    # 1. to fix the maximum pt for all fits (high pt saturation issue)
    # helps ease things into the right solution space
    # if fit_max > 650.0:
    #     print "*** WARNING: about to apply a JOE_HACK ***"
    #     print "*** lowers the upper limit of the fits to 650GeV ***"
    #     fit_max = 650.0
    # 2. to change the auto settings for a troublesome eta bin 
    #if absetamin == 2.5:
    #    print "*** WARNING: about to apply a JOE_HACK ***"
    #    print "*** messing with fit limits for 2.500<|eta|<2.964 ***"
    #    max_ind = 80
    #    fit_max = xarr[max_ind]
    #    print max_ind
    #    print fit_max
    #    fit_min = 40.0
    #    min_ind = 0
    if absetamin == 3.489:
        print "* WARNING: about to apply a JOE_HACK *"
        print "* messing with fit limits for 3.489<|eta|<4.191 *"
        max_ind = 17
        fit_max = xarr[max_ind]
        print max_ind
        print fit_max
        fit_min = 40.0
        min_ind = 0
<<<<<<< HEAD
    if absetamin == 2.964:
        print "* WARNING: about to apply a JOE_HACK *"
        print "* messing with fit limits for 2.964<|eta|<3.489 *"
        max_ind = 17
        fit_max = xarr[max_ind]
        print max_ind
        print fit_max
        fit_min = 40.0
        min_ind = 0
    if absetamin == 3.489:
        print "* WARNING: about to apply a JOE_HACK *"
        print "* messing with fit limits for 3.489<|eta|<4.191 *"
        max_ind = 17
        fit_max = xarr[max_ind]
        print max_ind
        print fit_max
        fit_min = 40.0
        min_ind = 0
=======
>>>>>>> aaad49d5608e2bb8cc2dcc646dc45f32875dab93
    if absetamin == 4.191:
        print "* WARNING: about to apply a JOE_HACK *"
        print "* messing with fit limits for 4.191<|eta|<5.191 *"
        max_ind = 17
        fit_max = xarr[max_ind]
        print max_ind
        print fit_max
        fit_min = 40.0                                                                                   
        min_ind = 0
    ###############
    ###############

    if fit_min > fit_max:
        raise RuntimeError('fit_min > fit_max! (%f > %f)' % (fit_min, fit_max))

    print "Correction fn fit range:", fit_min, fit_max

    # Generate a correction function with suitable range
    this_fit = function.Clone(function.GetName() + 'eta_%g_%g' % (absetamin, absetamax))
    this_fit.SetRange(fit_min, fit_max)

    # Make a sub-graph with only the points used for fitting
    # Do not user graph.RemovePoint()! It doesn't work, and only removes every other point
    # Instead make a graph with the bit of array we want
    fit_graph = ROOT.TGraphErrors(max_ind + 1 - min_ind,
                                  np.array(xarr[min_ind:max_ind + 1]),
                                  np.array(yarr[min_ind:max_ind + 1]),
                                  np.array(exarr[min_ind:max_ind + 1]),
                                  np.array(eyarr[min_ind:max_ind + 1]))
    fit_graph.SetName(graph.GetName() + "_fit")

    return fit_graph, this_fit


def fit_correction(graph, function, fit_min=-1, fit_max=-1):
    """
    Fit response curve with given correction function, within given bounds.
    If fit_min and fit_max are < 0, then use the range of the function supplied.

    Note that sometime the fit fails - if so, we try raising the lower
    bound of the fit until it suceeds (sometimes it works at e.g. 45, but not 40).
    If that fails, then we lower the upper bound and try fitting, raising
    the lower bound again if necessary. Iterative process, so fairly slow.

    Note that the 'stepping' is done in terms of the graph points, so non-uniform.

    We stop when the upper bound of the fit approaches the original lower bound.

    Returns graph (with fitted function) and parameters of successful fit if
    successful (otherwise an empty list).
    """
    # Get the min and max of the fit function if the user didn't define it
    if fit_min < 0 and fit_max < 0:
        fit_min, fit_max = ROOT.Double(), ROOT.Double()
        function.GetRange(fit_min, fit_max)

    print "Fitting", fit_min, fit_max

    # Now do the fitting, incrementing the fit min if failure
    fit_result = -1

    xarr, yarr = cu.get_xy(graph)

    # Keep the points in the graph closest to the min/max values
    # (and the index of the point in the graph array) for reference
    orig_fit_min_ind, orig_fit_min = closest_element(xarr, fit_min)
    orig_fit_max_ind, orig_fit_max = closest_element(xarr, fit_max)
    fit_min_ind, fit_max_ind = orig_fit_min_ind, orig_fit_max_ind
    print 'Starting with fit range:', orig_fit_min, orig_fit_max

    while fit_max_ind - orig_fit_min_ind >= 5:
        fit_min_ind = orig_fit_min_ind
        while fit_min_ind + 5 < fit_max_ind:
            fit_min = xarr[fit_min_ind]
            fit_max = xarr[fit_max_ind]
            function.SetRange(fit_min, fit_max)

            mode = "QR"
            if str(function.GetExpFormula()).startswith("pol"):
                mode += "F"
            fit_result = int(graph.Fit(function.GetName(), mode, "", fit_min, fit_max))
            if fit_result != 0:
                fit_min_ind += 1
                continue

            # sanity check - sometimes will have status = 0 even though rubbish,
            if not check_sensible_function(function):
                fit_result = -1

            if fit_result == 0:
                print "Fit result:", fit_result, "for fit min", fit_min, "to max", fit_max
                break
            else:
                fit_min_ind += 1

        if fit_result == 0:
            break

        fit_max_ind -= 1
        print 'Trying with lowered fit_max:', xarr[fit_max_ind]

    params = []

    if fit_result != 0:
        print "Couldn't fit"
    else:
        for i in range(function.GetNumberFreeParameters()):
            params.append(function.GetParameter(i))

    return graph, params


def closest_element(arr, value):
    """Return (index, element) in array arr that is closest to value"""
    diff_abs = np.abs(arr - value * np.ones_like(len(arr)))
    min_diff = np.min(diff_abs)
    ind = list(diff_abs).index(min_diff)
    return ind, arr[ind]


def check_sensible_function(function, lim=[3, 1000], spacing=0.05):
    """Check if function is sensible. i.e. no large jumps or poles

    lim is a tuple or list of the lower and upper bounds to check over
    """
    for x in np.linspace(lim[0], lim[1], ((lim[1] - lim[0]) / spacing) + 1):
        if function.Eval(x) > 10 or function.Eval(x) < 0.5:
            return False
    return True


def redo_correction_fit(inputfile, outputfile, absetamin, absetamax, fitfcn):
    """Redo correction fit for a given eta bin.

    Get TGraphErrors for the bin, and perform calibration curve fitting
    procedure and save if successful.

    inputfile: TFile. The output file from running runCalibration.py previously.
    outputfile: TFile. The file you want to write the new graph & fit to.
    Can be the same as inputfile.
    absetamin: double
    absetamax: double
    fitfcn: TF1
    """
    # Get relevant graph
    gr = cu.get_from_file(inputfile, generate_eta_graph_name(absetamin, absetamax))
    outputfile.WriteTObject(gr, gr.GetName(), 'Overwrite')  # the original graph

    # Setup fitting (calculate sensible range, make sub-graph), then do fit!
    sub_graph, this_fit = setup_fit(gr, fitfcn, absetamin, absetamax, outputfile)
    fit_graph, fit_params = fit_correction(sub_graph, this_fit)
    outputfile.WriteTObject(this_fit, this_fit.GetName(), 'Overwrite')  # function by itself
    outputfile.WriteTObject(fit_graph, fit_graph.GetName(), 'Overwrite')  # has the function stored in it as well
    return fit_params


def main(in_args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="input ROOT filename")
    parser.add_argument("output", help="output ROOT filename")
    parser.add_argument("--no-genjet-plots", action='store_false',
                        help="Don't do genjet plots for each pt/eta bin")
    parser.add_argument("--no-correction-fit", action='store_false',
                        help="Don't do fits for correction functions")
    parser.add_argument("--redo-correction-fit", action='store_true',
                        help="Redo fits for correction functions")
    parser.add_argument("--inherit-params", action='store_true',
                        help='Use previous eta bins function parameters as starting point. '
                        'Helpful when fits not converging.')
    parser.add_argument("--burr", action='store_true',
                        help='Do Burr type 3 fit for response histograms instead of Gaus')
    parser.add_argument("--gct", action='store_true',
                        help="Load legacy GCT specifics e.g. fit defaults.")
    parser.add_argument("--stage1", action='store_true',
                        help="Load stage 1 specifics e.g. fit defaults.")
    parser.add_argument("--stage2", action='store_true',
                        help="Load stage 2 specifics e.g. fit defaults, pt bins.")
    parser.add_argument("--central", action='store_true',
                        help="Do central eta bins only (eta <= 3)")
    parser.add_argument("--forward", action='store_true',
                        help="Do forward eta bins only (eta >= 3)")
    parser.add_argument("--PUmin", type=float, default=-100,
                        help="Minimum number of PU vertices (refers to *actual* "
                        "number of PU vertices in the event, not the centre "
                        "of of the Poisson distribution)")
    parser.add_argument("--PUmax", type=float, default=1200,
                        help="Maximum number of PU vertices (refers to *actual* "
                        "number of PU vertices in the event, not the centre "
                        "of of the Poisson distribution)")
    parser.add_argument("--etaInd", nargs="+",
                        help="list of eta bin INDICES to run over - "
                        "if unspecified will do all. "
                        "This overrides --central/--forward. "
                        "Handy for batch mode. "
                        "IMPORTANT: MUST PUT AT VERY END")
    args = parser.parse_args(args=in_args)
    print args

    if args.stage2:
        print "Running with Stage2 defaults"
    elif args.stage1:
        print "Running with Stage1 defaults"
    elif args.gct:
        print "Running with GCT defaults"
    else:
        raise RuntimeError("You need to specify defaults: --gct/--stage1/--stage2")

    # Turn off gen plots if you don't want them - they slow things down,
    # and don't affect determination of correction fn
    do_genjet_plots = args.no_genjet_plots
    if not do_genjet_plots:
        print "Not producing genjet plots"

    # Turn off if you don't want to fit to the correction curve
    # e.g. if you're testing your calibrations, since it'll waste time
    do_correction_fit = args.no_correction_fit
    if not do_correction_fit:
        print "Not fitting correction curves"

    if args.burr:
        print 'Using Burr Type3 for response hist fits'

    # Open input & output files, check
    print "IN:", args.input
    print "OUT:", args.output
    if (args.redo_correction_fit and
        os.path.realpath(args.input) == os.path.realpath(args.output)):
        input_file = cu.open_root_file(args.input, "UPDATE")
        output_file = input_file
    else:
        input_file = cu.open_root_file(args.input, "READ")
        output_file = cu.open_root_file(args.output, "RECREATE")

    # Figure out which eta bins the user wants to run over
    etaBins = binning.eta_bins
    if args.etaInd:
        args.etaInd.append(int(args.etaInd[-1]) + 1)  # need upper eta bin edge
        etaBins = [etaBins[int(x)] for x in args.etaInd]
    elif args.central:
        etaBins = [eta for eta in etaBins if eta < 3.1]
    elif args.forward:
        etaBins = [eta for eta in etaBins if eta > 2.9]
    print "Running over eta bins:", etaBins

    # Store last set of fit params if the user is doing --inherit-param
    previous_fit_params = []

    # Do plots & fitting to get calib consts
    for i, (eta_min, eta_max) in enumerate(pairwise(etaBins)):
        print "Doing eta bin: %g - %g" % (eta_min, eta_max)

        # whether we're doing a central or forward bin (.01 is for rounding err)
        forward_bin = eta_max > 3.01

        # setup pt bins, wider ones for forward region
        # ptBins = binning.pt_bins if not forward_bin else binning.pt_bins_wide
        ptBins = binning.pt_bins_stage2 if not forward_bin else binning.pt_bins_stage2_hf

        # Load fit function & starting params - important as wrong starting params
        # can cause fit failures
        default_params = []
        if args.stage2:
            default_params =STAGE2_DEFAULT_PARAMS_SELECT # this is selected around line 90
        elif args.stage1:
            default_params = STAGE1_DEFAULT_PARAMS
        elif args.gct:
            default_params = GCT_DEFAULT_PARAMS

        # Ignore the genric fit defaults and use the last fit params instead
        if args.inherit_params and previous_fit_params != []:
            print "Inheriting params from last fit"
            default_params = previous_fit_params[:]

        fitfunc = central_fit_select # this is selected around line 90
        set_fit_params(fitfunc, default_params)

        # Actually do the graph making and/or fitting!
        if args.redo_correction_fit:
            fit_params = redo_correction_fit(input_file, output_file, eta_min, eta_max, fitfunc)
        else:
            fit_params = make_correction_curves(input_file, output_file, ptBins, eta_min, eta_max,
                                                fitfunc, do_genjet_plots, do_correction_fit,
                                                args.PUmin, args.PUmax, args.burr)
        # Save successful fit params
        if fit_params != []:
            previous_fit_params = fit_params[:]

    input_file.Close()
    output_file.Close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
