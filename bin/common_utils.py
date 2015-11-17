"""Set of common functions that are used in loads of scripts."""


import ROOT
import os
from subprocess import call
from sys import platform as _platform
import numpy as np


ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.TH1.SetDefaultSumw2(True)


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
            raise RuntimeError("No such file %s" % filename)
    f = ROOT.TFile(filename, mode)
    if f.IsZombie() or not f:
        raise RuntimeError("Can't open TFile %s" % filename)
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
        raise Exception("Can't get object named %s from %s" % (obj_name, tfile.GetName()))
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


def norm_vertical_bins(hist):
    """
    Return a copy of the 2D hist, with x bin contents normalised to 1.
    This way you can clearly see the distribution per x bin,
    rather than underlying distribution across x bins.
    """

    h = hist.Clone(hist.GetName() + "_normX")
    nbins_y = h.GetNbinsY()
    for i in xrange(1, h.GetNbinsX() + 1, 1):
        y_int = h.Integral(i, i + 1, 1, nbins_y)
        if y_int != 0:
            scale_factor = 1. / y_int
            for j in xrange(1, nbins_y + 1, 1):
                h.SetBinContent(i, j, h.GetBinContent(i, j) * scale_factor)
                h.SetBinError(i, j, h.GetBinError(i, j) * scale_factor)

    return h
