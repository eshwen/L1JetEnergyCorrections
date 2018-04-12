"""Set of common functions that are used in loads of scripts."""


import ROOT
import os
from subprocess import call
from sys import platform as _platform
import numpy as np
import math
import argparse


ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.TH1.SetDefaultSumw2(True)


class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    """Make argparse respect space formatting (newlines, etc) AND show defaults"""
    pass


def open_pdf(pdf_filename):
    """Open a PDF file using system's default PDF viewer."""
    if _platform.startswith("linux"):
        # linux
        call(["xdg-open", pdf_filename])
    elif _platform == "darwin":
        # OS X
        call(["open", pdf_filename])
    elif _platform == "win32":
        # Windows
        call(["start", pdf_filename])


#
# Filepath/directory fns
#
def cleanup_filepath(filepath):
    """Resolve any env vars, ~, etc, and return absolute path."""
    return os.path.abspath(os.path.expandvars(os.path.expanduser(filepath)))


def get_full_path(filepath):
    """Return absolute directory of filepath.
    Resolve any environment vars, ~, sym links(?)"""
    return os.path.dirname(cleanup_filepath(filepath))


def check_file_exists(filepath):
    """Check if file exists. Can do absolute or relative file paths."""
    return os.path.isfile(cleanup_filepath(filepath))


def check_dir_exists(filepath):
    """Check if directory exists."""
    return os.path.isdir(cleanup_filepath(filepath))


def check_dir_exists_create(filepath):
    """Check if directory exists. If not, create it."""
    if not check_dir_exists(filepath):
        os.makedirs(cleanup_filepath(filepath))


#
# ROOT specific fns, like opening files safely
#
def open_root_file(filename, mode="READ"):
    """Safe way to open ROOT file. Could be improved."""
    if mode in ["READ", "UPDATE"]:
        if not check_file_exists(filename):
            raise IOError("No such file %s" % filename)
    f = ROOT.TFile(filename, mode)
    if f.IsZombie() or not f:
        raise IOError("Can't open TFile %s" % filename)
    return f


def exists_in_file(tfile, obj_name):
    """Check if object exists in TFile.

    Also handles directory structure, e.g. histograms/central/pt_1
    """
    parts = obj_name.split("/")
    current_obj = tfile
    for p in parts:
        if current_obj.GetListOfKeys().Contains(p):
            current_obj = current_obj.Get(p)
        else:
            return False
    return True


def get_from_file(tfile, obj_name, info=False):
    """Get some object from ROOT TFile with checks."""
    if info:
        print "Getting %s" % obj_name
    if not exists_in_file(tfile, obj_name):
        raise IOError("Can't get object named %s from %s" % (obj_name, tfile.GetName()))
    else:
        return tfile.Get(obj_name)


def check_exp(n):
    """
    Checks if number has stupidly larger exponent

    Can occur is using buffers - it just fills unused bins with crap
    """

    from math import fabs, log10, frexp
    m, e = frexp(n)
    return fabs(log10(pow(2, e))) < 10


def get_xy(graph):
    """
    Return lists of x, y points from a graph, because it's such a PITA
    """
    xarr = list(np.ndarray(graph.GetN(), 'd', graph.GetX()))
    yarr = list(np.ndarray(graph.GetN(), 'd', graph.GetY()))
    return xarr, yarr


def get_exey(graph):
    """
    Return lists of errors on x, y points from a graph, because it's such a PITA
    """
    xarr = list(np.ndarray(graph.GetN(), 'd', graph.GetEX()))
    yarr = list(np.ndarray(graph.GetN(), 'd', graph.GetEY()))
    return xarr, yarr


def norm_vertical_bins(hist, rescale_peaks=False):
    """Return a copy of the 2D hist, with x bin contents normalised to 1.
    This way you can clearly see the distribution per x bin,
    rather than underlying distribution across x bins.

    Parameters
    ----------
    hist : ROOT.TH2
        2D histogram to use
    rescale_peaks : bool, optional
        Scales all bin contents such that all x bins have the same peak value.
        This way the colour system works across all bins, but absolute values
        are useless.
    """

    hnew = hist.Clone(hist.GetName() + "_normX")
    nbins_y = hnew.GetNbinsY()
    maximums = []
    for i in range(1, hnew.GetNbinsX() + 1, 1):
        y_int = hnew.Integral(i, i + 1, 1, nbins_y)
        peak = 0
        if y_int > 0:
            scale_factor = 1. / y_int
            for j in range(1, nbins_y + 1, 1):
                if hnew.GetBinContent(i, j) > 0:
                    new_bin_value = hist.GetBinContent(i, j) * scale_factor
                    if new_bin_value > peak:
                        peak = new_bin_value
                    hnew.SetBinContent(i, j, new_bin_value)
                    hnew.SetBinError(i, j, hist.GetBinError(i, j) * scale_factor)
        maximums.append(peak)

    # Rescale so all peaks have same value = same color
    if rescale_peaks:
        max_peak = max(maximums)
        for i in range(1, hnew.GetNbinsX() + 1, 1):
            if maximums[i - 1] == 0:
                continue
            sf = 1. * max_peak / maximums[i - 1]
            for j in range(1, hnew.GetNbinsY()):
                if hnew.GetBinContent(i, j) > 0:
                    hnew.SetBinContent(i, j, hnew.GetBinContent(i, j) * sf)
                    hnew.SetBinError(i, j, hist.GetBinError(i, j) * sf)

    # rescale Z axis otherwise it just removes a lot of small bins
    # set new minimum such that it includes all points, and the z axis min is
    # a negative integer power of 10
    min_bin = hnew.GetMinimum(0)
    max_bin = max(maximums) if rescale_peaks else hnew.GetMaximum()
    max_bin = hnew.GetMaximum()
    hnew.SetAxisRange(10**math.floor(math.log10(min_bin)), max_bin, 'Z')
    return hnew
