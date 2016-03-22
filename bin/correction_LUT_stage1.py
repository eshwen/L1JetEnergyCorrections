"""Functions for printing LUT for Stage 1"""


import ROOT
from itertools import izip
import os
import common_utils as cu
import numpy as np
from collections import OrderedDict


class MultiFunc(object):
    """Class to handle using different TF1s over different ranges.

    E.g. y = x for x = [0,1], then y = x^2 for [1, Inf]
    This was created since it is so hard (impossible?) to do in ROOT.

    It is supposed to ducktype TF1, although so far only bare basics implemented.
    """

    def __init__(self, functions_dict):
        """Constructor takes as argument a dictionary, where each key is a tuple,
        and each value is a TF1 object.

        The tuple must have 2 elements: lower and upper bounds, which define the
        valid function range.

        e.g.
        lin = ROOT.TF1("lin", "x")
        quad = ROOT.TF1("quad", "x*x")

        functions_dict = {
            (-np.inf, 1): lin,
            (1, np.inf): quad
        }
        f = c.MultiFunc(functions_dict)
        f.Eval(0.5) # 0.5
        f.Eval(3) # 9
        """
        # Need a OrderedDict to keep ordered by application range
        self.functions_dict = OrderedDict(sorted(functions_dict.items(), key=lambda x: x[0][0]))

    def Eval(self, x):
        """Emulate TF1.Eval() but will call the correct function,
        depending on which function is applicable for the value of x."""
        return [func for lim, func in self.functions_dict.iteritems() if lim[0] <= x < lim[1]][0].Eval(x)

    def Draw(self, args=None):
        """Draw the various functions"""

        if "SAME" not in args:
            # make a 'blank' function to occupy the complete range of x values:
            lower_lim = min([lim[0] for lim in self.functions_dict.keys()])
            if np.isneginf(lower_lim):
                lower_lim = -999
            upper_lim = max([lim[1] for lim in self.functions_dict.keys()])
            if np.isposinf(lower_lim):
                upper_lim = 999
            blank = ROOT.TF1("blank" + str(np.random.randint(0, 10000)), "1.5", lower_lim, upper_lim)
            blank.Draw()
            max_value = max([func.GetMaximum(lim[0], lim[1])
                             for lim, func in self.functions_dict.iteritems()]) * 1.1
            blank.SetMaximum(max_value)
            min_value = min([func.GetMinimum(lim[0], lim[1])
                             for lim, func in self.functions_dict.iteritems()]) * 0.9
            blank.SetMinimum(min_value)
            ROOT.SetOwnership(blank, False)  # NEED THIS SO IT ACTUALLY GETS DRAWN. SERIOUSLY, WTF?!
            blank.SetLineColor(ROOT.kWhite)

        # now draw the rest of the functions
        args = "" if not args else args
        for func in self.functions_dict.values():
            func.Draw("SAME" + args)

    def __str__(self):
        """str representation. Prints each fns name and range of validity,
        ordered by ascending range
        """
        parts = ["%s: %.2f - %.2f\n%s" % (f.GetName(), r[0], r[1], f.GetExpFormula())
                 for r, f in self.functions_dict.iteritems()]
        return "\n".join(sorted(parts))


def print_Stage1_lut_file(fit_functions, filename, plot=True):
    """
    Take fit functions, converts to LUT for use in CMSSW config file with Stage
    1 emulator, and pints to file.

    fit_functions is a list, where each entry is an object that returns a
    correction value when its Eval() method is called. (e.g. TF1, MultiFunc)

    The order MUST be in physical eta, so the first entry coveres 0 - 0.348, etc

    plot is a bool, if True then it'll print a 2D coloured plot of the
    post-calib ranks for each pt,eta bin. Designed so you can visually check
    everything looks sensible.

    Note that the LUT has entries for both + and - eta. It refers to eta by
    region number (0 - 21), *not* physical eta. Thus the first bin for the
    LUT must be for physical eta 4.5 - 5, NOT 0 - 0.348.
    Don't worry, this method handles that conversion.

    Please update the header if necessary - check with Len.

    Adapted from code originally by Maria Cepeda.
    """

    print "Making Stage 1 LUT..."

    lut_plot = None
    if plot:
        plot_title = "%s;HW pT pre;eta" % os.path.basename(filename)
        lut_plot = ROOT.TH2D("lut_plot", plot_title, 1025, 0, 1025, 22, 0, 22)

    with open(filename, "w") as lut_file:
        with open(filename.replace(".txt", "_dump.txt"), "w") as dump_file:
            header = """#<header> V1 15 7 </header>
########################################
# jet calibration and ranking LUT
# MSB 5 bits are eta value, LSB 10 bits
# are jet pt (not 14!, make sure to cap)
########################################
# Second  attempt at preliminar CalibJet for FirmwareVersion3
# Symmetric in Eta and RANK=0 jets do not scale up
#########################################
"""
            lut_file.write(header)

            for eta in xrange(22):

                param_ind = (10 - eta) if eta < 11 else (eta - 11)
                print "Eta region:", eta, " = physical eta bin:", param_ind
                for pt in xrange(1025):

                    if pt > (1<<10) - 1:
                        pt = ((1<<10) - 1)
                        break

                    lut_address = (eta<<10) + pt
                    physPt = pt / 2.  # convert HW pt to physical pt
                    corr = fit_functions[param_ind].Eval(physPt)
                    pt_corr = physPt * corr
                    if pt_corr < 0:  # avoid -ve pt
                        pt_corr = 0
                    RANKCALIB = int(pt_corr / 4)  # The 4 is to go to the 4 GeV binning at the GT
                    if (RANKCALIB > 63):  # cap pt
                        RANKCALIB = 63
                    line = "%s %s\n" % (lut_address, RANKCALIB)
                    lut_file.write(line)
                    # dump_line = "eta: %d phys pt: %f LUT address: %d corrValue: %f " \
                    #             "corrPhysPt: %f RANKCALIB: %d\n" % (eta,
                    #                                                 physPt,
                    #                                                 lut_address,
                    #                                                 corr,
                    #                                                 pt_corr,
                    #                                                 RANKCALIB)
                    dump_dict = {'eta': eta, 'physPt': physPt, 'lut': lut_address,
                                 'corr': corr, 'pt_corr': pt_corr, 'rank': RANKCALIB}
                    dump_line = "eta: ${eta:d} phys pt: ${physPt:f} " \
                                "LUT address: ${lut:d} corrValue: ${corr:f} " \
                                "corrPhysPt: ${pt_corr:f} RANKCALIB: ${rank:d}\n".format(dump_dict)

                    dump_file.write(dump_line)
                    if plot:
                        # +1 as ROOT bins start at 1, not 0!
                        lut_plot.SetBinContent(pt + 1, eta + 1, RANKCALIB)

    if plot:
        c = ROOT.TCanvas("c", "", 800, 500)
        c.SetTicks(0)
        ROOT.gStyle.SetNumberContours(63)
        ROOT.gStyle.SetPalette(55)
        lut_plot.SetMarkerSize(1)
        lut_plot.Draw("COLZ")
        # Here we try and be intelligent - find the minimum pt above which all
        # eta and pt have bincontent = 63
        max_pt = 0
        for i in xrange(1, lut_plot.GetNbinsX() + 1):
            all_max = True
            for j in xrange(1, lut_plot.GetNbinsY() + 1):
                if lut_plot.GetBinContent(i, j) != 63:
                    all_max = False
                    break
            if all_max:
                max_pt = i
                break

        lut_plot.SetAxisRange(0, max_pt, "X")
        xtitle = lut_plot.GetXaxis().GetTitle()
        xtitle += "(RANKCALIB = 63 for pt > %d for all eta)" % max_pt
        lut_plot.GetXaxis().SetTitle(xtitle)
        lut_plot.GetZaxis().SetTitle("RANK CALIB")
        lut_plot.GetZaxis().SetTitleOffset(0.58)
        c.SaveAs(os.path.splitext(filename)[0] + ".pdf")


def make_fancy_fits(fits, graphs, condition=0.1):
    """
    Make fancy fit, by checking for deviations between graph and fit at low pT.
    Then below the pT where they differ, just use the last good correction factor.

    This generates a new set of correction functions, represented by MultiFunc objects.


    Parameters
    ----------
    fits : list[TF1]
        List of fit functions, one per eta bin.
    graphs : list[TGraph]
        List of graphs, one per eta bin.
    condition : float
        Fractional difference between graph & curve to determine where curve
        becomes a constant value.
    """
    print "Making fancy fits..."

    new_functions = []

    for i, (fit, gr) in enumerate(zip(fits, graphs)):
        x_arr, y_arr = cu.get_xy(gr)
        # ex_arr, ey_arr = cu.get_exey(gr)

        pt_merge = 0
        corr_merge = 0

        print "Eta bin", str(i)
        # print "pt, correction acc. to graph, correcction acc. to fit, diff"

        for j, (pt, corr) in enumerate(izip(x_arr[::-1], y_arr[::-1])):
            # Loop through each point of the graph in reverse,
            # only considering points with pt < 40.
            # Determine where the function and graph separate by
            # looking at the difference.
            if pt > 40:
                continue
            # print pt, corr, fit.Eval(pt), abs(fit.Eval(pt) - corr)
            # Determine where to start plateau:
            if abs(fit.Eval(pt) - corr) > condition:
                break
            else:
                pt_merge = pt
                corr_merge = fit.Eval(pt)

        print "pt_merge:", pt_merge, "corr fn value:", fit.Eval(pt_merge)

        # Make our new 'frankenstein' function: constant for pt < pt_merge,
        # then the original function for pt > pt_merge
        constant = ROOT.TF1("constant%d" % i, "%.8f" % corr_merge, 0, pt_merge)
        constant.SetParameter(0, corr_merge)

        function_str = "[0]+[1]/(pow(log10(x),2)+[2])+[3]*exp(-[4]*(log10(x)-[5])*(log10(x)-[5]))"
        for p in xrange(fit.GetNumberFreeParameters()):
            function_str = function_str.replace("[%d]" % p, "%.8f" % fit.GetParameter(p))
        fit_new = ROOT.TF1("fitfcn%d" % i, function_str, pt_merge * 0.8, 512)
        # set lower range below pt_merge just for drawing purposes

        # Make a MultiFunc object to handle the different functions operating
        # over different ranges since TF1 can't do this.
        # Maybe ROOFIT can?
        functions_dict = {(0, pt_merge): constant,
                          (pt_merge, 512): fit_new}
        total_fit = MultiFunc(functions_dict)
        new_functions.append(total_fit)

    return new_functions
