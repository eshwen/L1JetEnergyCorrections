#!/usr/bin/env python
"""
This script produces plots for showing off in notes/presentations, etc.

Deisgned to be quick! So just pull the histograms, apply some aesthetics, save.

It takes in ROOT files made by:
- RunMatcher
- makeResolutionPlots.py
- checkCalibration.py
- runCalibration.py

Robin Aggleton

run with:
$ python /users/jt15104/CMSSW_8_0_9/src/L1Trigger/L1JetEnergyCorrections/bin/showoffPlots.py --checkcal <checkcalfile.root>

"""


import ROOT
import sys
import binning
from binning import pairwise
import argparse
from itertools import izip, product
import common_utils as cu
from array import array
import os
from runCalibration import generate_eta_graph_name
from subprocess import check_output
from shutil import make_archive
from distutils.spawn import find_executable


ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.TH1.SetDefaultSumw2(True)
ROOT.gStyle.SetOptFit(1)  # only show fit params and errors
# ROOT.gStyle.SetOptStat(0)
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetPalette(55)
ROOT.gErrorIgnoreLevel = ROOT.kWarning # turn off the printing output

#################################################
# Some common strings
# Note that l1_str and ref_str can be overridden
# using the --l1str and --refstr args
#################################################
l1_str = 'L1'
#l1_str = 'PF'
#l1_str = 'Offline CaloJet'

#ref_str = 'GenJet'
ref_str = 'PFJet'
#ref_str = 'Offline CaloJet'

# Some common axis labels
rsp_str = "E_{T}^{%s}/E_{T}^{%s}" % (l1_str, ref_str)
eta_str = "#eta"
eta_ref_str = "|#eta^{%s}|" % (ref_str)
eta_l1_str = "|#eta^{%s}|" % (l1_str)
dr_str = "#DeltaR(%s jet, Ref jet)" % (l1_str)
pt_str = "E_{T}[GeV]"
pt_l1_str = "E_{T}^{%s} [GeV]" % (l1_str)
pt_ref_str = "E_{T}^{%s} [GeV]" % (ref_str)
res_l1_str = "#sigma(E_{T}^{%s} - E_{T}^{%s})/<E_{T}^{%s}>" % (l1_str, ref_str, l1_str)
res_ref_str = "#sigma(E_{T}^{%s} - E_{T}^{%s})/<E_{T}^{%s}>" % (l1_str, ref_str, ref_str)
alt_res_l1_str = "(E_{T}^{%s} - E_{T}^{%s})/E_{T}^{%s}" % (l1_str, ref_str, l1_str)
pt_diff_str = "E_{T}^{%s} - E_{T}^{%s} [GeV]" % (l1_str, ref_str)

# min/max response for responve vs X graphs
# rsp_min, rsp_max = 0.2, 1.5
rsp_min, rsp_max = 0, 2
# rsp_min, rsp_max = 0.75, 1.25

#############################################
# LABELS, COLOURS, AND TITLE ON PLOTS
# NB title can be overridden using --title <str>
#############################################
# plot_title = "Run 260627, Stage 2, no L1JEC, with PF cleaning"
# plot_title = "Run 260627 SingleMu, Stage 2, with L1JEC, with PF cleaning"

# plot_title = "Spring15 MC, Stage 2, no JEC"
# plot_title = "Spring15 MC, Stage 2, with L1JEC"
# plot_title = "Spring15 MC, Stage 2, with L1JEC (LUT)"
# plot_title = "Spring15 MC, ak4PFCHS vs ak4GenJets, no PF cleaning"
# plot_title = "Spring15 MC, Stage2, L1 vs ak4PFCHS, no PF cleaning"

# plot_title = "Fall15 MC, 45-55PU, Stage 2, no L1JEC"
# plot_title = "Fall15 MC, 0PU, Stage 2, with L1JEC"
plot_title = "Spring18 MC, no PU specified, Stage 2"

# plot_title = "ttH, H #to bb MC, 30PU, Stage 2, no L1JEC (derived from Spring15)"
# plot_title = "ttH, H #to bb MC, 30PU, Stage 2, with L1JEC (derived from Spring15)"

plot_colors = [ROOT.kRed, ROOT.kBlue, ROOT.kGreen + 2, 8]
plot_markers = [20, 21, 22, 23]


def generate_canvas(title=""):
    """Generate a standard TCanvas for all plots"""
    c = ROOT.TCanvas("c", title, 1200, 900)
    c.SetTicks(1, 1)
    return c


def generate_legend(x1=0.34, y1=0.7, x2=0.88, y2=0.88):
    """Generate a standard TLegend. Can optionally pass in co-ordinates. """
    leg = ROOT.TLegend(x1, y1, x2, y2)
    return leg

#############################################
# PLOTS USING OUTPUT FROM RunMatcher
#############################################

def plot_dR(tree, oDir, cut="1", eta_min=0, eta_max=5, oFormat="pdf"):
    """Plot deltaR(L1 - RefJet)"""
    c = generate_canvas()
    tree.Draw("dr>>h_dr(40,0,0.8)", cut + "&& TMath::Abs(eta)>%g && TMath::Abs(eta)<%g" % (eta_min, eta_max), "HISTE")
    h_dr = ROOT.gROOT.FindObject("h_dr")
    h_dr.SetTitle(cut + "&& TMath::Abs(eta)>%g && TMath::Abs(eta)<%g;%s;N" % (eta_min, eta_max, dr_str))
    c.SaveAs("%s/dr_%g_%g.%s" % (oDir, eta_min, eta_max, oFormat))


def plot_pt_l1(tree, oDir, cut="1", eta_min=0, eta_max=5, oFormat="pdf"):
    """Plot pT(L1)"""
    c = generate_canvas()
    tree.Draw("pt>>h_pt(63,0,252)", cut + "&& TMath::Abs(eta)>%g && TMath::Abs(eta)<%g" % (eta_min, eta_max), "HISTE")
    h_pt = ROOT.gROOT.FindObject("h_pt")
    h_pt.SetTitle(cut + "&& TMath::Abs(eta)>%g && TMath::Abs(eta)<%g;%s;N" % (eta_min, eta_max, pt_l1_str))
    c.SaveAs("%s/pt_l1_%g_%g.%s" % (oDir, eta_min, eta_max, oFormat))


def plot_eta_l1(tree, oDir, cut="1", oFormat="pdf"):
    """Plot eta(L1)"""
    c = generate_canvas()
    h_eta = ROOT.TH1D("h_eta", "%s;%s;N" % (cut, eta_l1_str),
                      len(binning.eta_bins_all) - 1, array('d', binning.eta_bins_all))
    tree.Draw("eta>>h_eta", cut, "HISTE")
    c.SaveAs("%s/eta_l1.%s" % (oDir, oFormat))


def plot_pt_ref(tree, oDir, cut="1", eta_min=0, eta_max=5, oFormat="pdf"):
    """Plot pT(Reference)"""
    c = generate_canvas()
    tree.Draw("ptRef>>h_pt(63,0,252)", cut + "&& TMath::Abs(eta)>%g && TMath::Abs(eta)<%g" % (eta_min, eta_max), "HISTE")
    h_pt = ROOT.gROOT.FindObject("h_pt")
    h_pt.SetTitle(cut + "&& TMath::Abs(eta)>%g && TMath::Abs(eta)<%g;%s;N" % (eta_min, eta_max, pt_ref_str))
    c.SaveAs("%s/pt_ref_%g_%g.%s" % (oDir, eta_min, eta_max, oFormat))


def plot_eta_ref(tree, oDir, cut="1", oFormat="pdf"):
    """Plot eta(Reference)"""
    c = generate_canvas()
    h_eta = ROOT.TH1D("h_eta", "%s;%s;N" % (cut, eta_ref_str),
                      len(binning.eta_bins_all) - 1, array('d', binning.eta_bins_all))
    tree.Draw("etaRef>>h_eta", cut, "HISTE")
    c.SaveAs("%s/eta_ref.%s" % (oDir, oFormat))


def plot_pt_both(tree, oDir, cut="1", eta_min=0, eta_max=5, oFormat="pdf"):
    """Plot pt(Reference) and pt(L1) on same plot"""
    c = generate_canvas()
    total_cut = cut + " && TMath::Abs(eta) > %g && TMath::Abs(eta) < %g" % (eta_min, eta_max)
    h_pt_l1 = ROOT.TH1D("h_pt_l1", "%s;%s;N" % (total_cut, pt_str), 63, 0, 252)
    h_pt_ref = ROOT.TH1D("h_pt_ref", "%s;%s;N" % (total_cut, pt_str), 63, 0, 252)
    tree.Draw("pt>>h_pt_l1", cut + " && TMath::Abs(eta) > %g && TMath::Abs(eta) < %g" % (eta_min, eta_max), "HISTE")
    tree.Draw("ptRef>>h_pt_ref", cut + " && TMath::Abs(eta) > %g && TMath::Abs(eta) < %g" % (eta_min, eta_max), "HISTE")
    h_pt_ref.SetLineColor(ROOT.kRed)
    stack = ROOT.THStack("st", "")
    stack.Add(h_pt_l1)
    stack.Add(h_pt_ref)
    stack.Draw("NOSTACK HISTE")
    print total_cut
    stack.GetHistogram().SetTitle("%s;%s;N" % (total_cut, pt_str))
    c.SetTitle(total_cut)
    leg = generate_legend()
    leg.AddEntry(0, "%s: %g - %g" % (eta_l1_str, eta_min, eta_max), "")
    leg.AddEntry(h_pt_l1, "L1", "L")
    leg.AddEntry(h_pt_ref, "Ref", "L")
    leg.Draw()
    c.SaveAs("%s/pt_both_%g_%g.%s" % (oDir, eta_min, eta_max, oFormat))


def plot_eta_both(tree, oDir, cut="1", oFormat="pdf"):
    """Plot eta(Reference) and eta(L1) on same plot"""
    c = generate_canvas()
    h_eta_l1 = ROOT.TH1D("h_eta_l1", "%s;%s;N" % (cut, eta_str),
                         len(binning.eta_bins_all) - 1, array('d', binning.eta_bins_all))
    h_eta_ref = ROOT.TH1D("h_eta_ref", "%s;%s;N" % (cut, eta_str),
                          len(binning.eta_bins_all) - 1, array('d', binning.eta_bins_all))
    tree.Draw("eta>>h_eta_l1", cut, "HISTE")
    tree.Draw("etaRef>>h_eta_ref", cut, "HISTE")
    h_eta_ref.SetLineColor(ROOT.kRed)
    h_eta_l1.Draw("HISTE")
    h_eta_ref.Draw("HISTE SAME")
    leg = generate_legend()
    leg.AddEntry(h_eta_l1, "L1", "L")
    leg.AddEntry(h_eta_ref, "Ref", "L")
    leg.Draw()
    c.SaveAs("%s/eta_both.%s" % (oDir, oFormat))


#############################################
# PLOTS USING OUTPUT FROM makeResolutionPlots
#############################################

def plot_pt_diff(res_file, eta_min, eta_max, pt_min, pt_max, oDir, oFormat="pdf"):
    """Plot the difference between L1 and ref jet pT, for given L1 pT, eta bin"""
    hname = "eta_%g_%g/Histograms/ptDiff_ref_%g_%g" % (eta_min, eta_max, pt_min, pt_max)
    h_diff = cu.get_from_file(res_file, hname)
    c = generate_canvas()
    h_diff.Draw()
    h_diff.SetMaximum(h_diff.GetMaximum() * 1.2)
    # h_diff.SetLineWidth(2)
    func = h_diff.GetListOfFunctions().At(0)
    func.SetLineWidth(1)
    h_diff.SetTitle("%g < %s < %g, %g < p_{T}^{%s} < %g;%s;N" % (eta_min, eta_l1_str, eta_max, pt_min, ref_str, pt_max, pt_diff_str))
    if not os.path.exists("%s/eta_%g_%g" % (oDir, eta_min, eta_max)):
        os.makedirs("%s/eta_%g_%g" % (oDir, eta_min, eta_max))
    c.SaveAs("%s/eta_%g_%g/pt_diff_eta_%g_%g_%g_%g.%s" % (oDir, eta_min, eta_max, eta_min, eta_max, pt_min, pt_max, oFormat))


def plot_res_pt_bin(res_file, eta_min, eta_max, pt_min, pt_max, oDir, oFormat="pdf"):
    """Plot the L1 resolution for given L1 pT, eta bin"""
    hname = "eta_%g_%g/Histograms/res_l1_%g_%g" % (eta_min, eta_max, pt_min, pt_max)
    h_res = cu.get_from_file(res_file, hname)
    c = generate_canvas()
    h_res.Draw()
    h_res.SetAxisRange(-2, 2, "X")
    h_res.SetTitle(";%s;N" % res_l1_str)
    c.SaveAs("%s/res_l1_eta_%g_%g_%g_%g.%s" % (oDir, eta_min, eta_max, pt_min, pt_max, oFormat))


def plot_ptDiff_Vs_pt(res_file, eta_min, eta_max, oDir, oFormat='pdf'):
    """Plot (ptL1 - pTRef) Vs pTL1 for given eta bin"""
    hname = "eta_%g_%g/Histograms/ptDiff_ref_2d" % (eta_min, eta_max)
    h_2d = cu.get_from_file(res_file, hname)
    c = generate_canvas()
    ROOT.gStyle.SetPalette(55)
    h_2d.RebinX(16)
    # h_2d.RebinY(2)
    h_2d.Draw("COLZ")
    h_2d.GetYaxis().SetRangeUser(-120, 120)
    c.SetLogz()
    c.SetTicks(1, 1)
    c.SaveAs("%s/h2d_ptDiff_ptRef_eta_%g_%g.%s" % (oDir, eta_min, eta_max, oFormat))


def plot_res_all_pt(res_file, eta_min, eta_max, oDir, oFormat="pdf"):
    """Plot a graph of resolution as a function of L1 eta."""

    c = generate_canvas()

    # binned by ref pt
    grname = "eta_%g_%g/resRefRef_%g_%g_diff" % (eta_min, eta_max, eta_min, eta_max)

    graph = cu.get_from_file(res_file, grname)
    # leg = generate_legend()
    mg = ROOT.TMultiGraph()
    i = 0
    graph.SetLineColor(plot_colors[i])
    graph.SetMarkerColor(plot_colors[i])
    graph.SetMarkerStyle(plot_markers[i])
    mg.Add(graph)
    # leg.AddEntry(graph, plot_labels[i], "LP")

    mg.Draw("ALP")
    mg.GetXaxis().SetTitleSize(0.04)
    mg.GetXaxis().SetTitleOffset(0.9)
    # mg.GetYaxis().SetTitle(res_l1_str)
    mg.GetYaxis().SetRangeUser(0, mg.GetYaxis().GetXmax() * 1.5)
    mg.GetYaxis().SetRangeUser(0, 0.6)
    mg.GetHistogram().SetTitle("%s;%s;%s" % (plot_title + ', %g < %s < %g' % (eta_min, eta_l1_str, eta_max), pt_ref_str, res_ref_str))
    mg.Draw("ALP")
    # leg.Draw()
    append = ""
    c.SaveAs("%s/res_ref_eta_%g_%g_diff%s.%s" % (oDir, eta_min, eta_max, append, oFormat))


def plot_eta_pt_rsp_2d(calib_file, etaBins, ptBins, oDir, oFormat='pdf'):
    """
    Plot a 2D map of response for each eta, pt bin. Display the <response> from
    Gaussian fit of response hist in that bin

    Uses the resolution output file, since this plot of rsp & fit for pT(L1) bin,
    and will be done for pre and post calib, whereas output from runCalibration
    will generally only be pre calib, and is binned by ref Jet pt
    """
    h_2d = ROOT.TH2D("h2d_eta_pt_rsp", ";%s;%s" % (pt_l1_str, eta_l1_str) ,
                     len(ptBins) - 1, array('d', ptBins),
                     len(etaBins) - 1, array('d', etaBins))
    for eta_ind, (eta_min, eta_max) in enumerate(zip(etaBins[:-1], etaBins[1:]), 1):
        for pt_ind, (pt_min, pt_max) in enumerate(zip(ptBins[:-1], ptBins[1:]), 1):
            h_rsp = cu.get_from_file(calib_file, "eta_%g_%g/Histograms/res_l1_%g_%g" % (eta_min, eta_max, pt_min, pt_max))
            if h_rsp.GetEntries() > 0:
                # we actually use the fit to (L1-Gen)/L1, so we need to * -1 and invert
                res = h_rsp.GetListOfFunctions().At(0).GetParameter(1)
                rsp = 1. / (1 - res)
                print rsp
                h_2d.SetBinContent(pt_ind, eta_ind, rsp)
            else:
                h_2d.SetBinContent(pt_ind, eta_ind, 0)
    c = generate_canvas()
    ROOT.gStyle.SetPaintTextFormat(".2f")
    ROOT.gStyle.SetPalette(56)
    h_2d.Draw("COLZTEXT")
    h_2d.GetZaxis().SetRangeUser(0, 2)
    c.SaveAs("%s/h2d_eta_pt_rsp.%s" % (oDir, oFormat))


#############################################
# PLOTS USING OUTPUT FROM checkCalibration
#############################################

def plot_rsp_eta_bin(calib_file, eta_min, eta_max, oDir, oFormat="pdf"):
    """Plot the response in one eta bin"""
    hname = "eta_%g_%g/Histograms/hrsp_eta_%g_%g" % (eta_min, eta_max, eta_min, eta_max)
    h_rsp = cu.get_from_file(calib_file, hname)
    func = h_rsp.GetListOfFunctions().At(0)
    c = generate_canvas()
    h_rsp.SetTitle(os.path.basename(hname) + ';response (%s)' % rsp_str)
    h_rsp.Draw("HISTE")
    if func:
        func.Draw("SAME")
    filename = "%s/h_rsp_%g_%g.%s" % (oDir, eta_min, eta_max, oFormat)
    c.SaveAs(filename)
    return filename


def plot_rsp_eta_bin_pt(calib_file, eta_min, eta_max, pt_var, pt_min, pt_max, oDir, oFormat="pdf"):
    """Plot the response in one eta bin with a pt cut"""
    if eta_max <= 3:
        # Quick and dirty correction to folder names, replacing 0_3 and 3_5 with more precise numbers
        hname = "eta_0_2.964/Histograms/hrsp_eta_%g_%g_%s_%g_%g" % (eta_min, eta_max, pt_var, pt_min, pt_max)
    else:
        hname = "eta_2.964_5.191/Histograms/hrsp_eta_%g_%g_%s_%g_%g" % (eta_min, eta_max, pt_var, pt_min, pt_max)
    try:
        h_rsp = cu.get_from_file(calib_file, hname)
    except Exception:
        return None
    func = h_rsp.GetListOfFunctions().At(0)
    c = generate_canvas()
    h_rsp.SetTitle(os.path.basename(hname) + ';response (%s)' % rsp_str)
    h_rsp.Draw("HISTE")
    if func:
        func.Draw("SAME")
    output_filename = "%s/h_rsp_%g_%g_%s_%g_%g.%s" % (oDir, eta_min, eta_max, pt_var, pt_min, pt_max, oFormat)
    c.SaveAs(output_filename)
    return output_filename


def plot_l1_Vs_ref(check_file, eta_min, eta_max, logZ, oDir, oFormat="pdf"):
    """Plot l1 pt against ref jet pt, for given L1 eta bin"""
    hname = "eta_%g_%g/Histograms/h2d_gen_l1" % (eta_min, eta_max)
    h2d_gen_l1 = cu.get_from_file(check_file, hname)
    c = generate_canvas()
    app = ""
    if logZ:
        c.SetLogz()
        app = "_log"
    h2d_gen_l1.SetTitle("%s: %g-%g;%s;%s" % (eta_l1_str, eta_min, eta_max, pt_ref_str, pt_l1_str))
    h2d_gen_l1.Draw("COLZ")
    max_pt = 512
    h2d_gen_l1.SetAxisRange(0, max_pt, 'X')
    h2d_gen_l1.SetAxisRange(0, max_pt, 'Y')
    # lines of constant response
    line1 = ROOT.TLine(0, 0, max_pt, max_pt)
    line1.SetLineStyle(1)
    line1.SetLineWidth(2)
    line1.Draw()

    line1p25 = ROOT.TLine(0, 0, max_pt / 1.25, max_pt)
    line1p25.SetLineWidth(2)
    # line1p25.Draw()

    line1p5 = ROOT.TLine(0, 0, max_pt / 1.5, max_pt)
    line1p5.SetLineWidth(2)
    # line1p5.Draw()

    line0p75 = ROOT.TLine(0, 0, max_pt, max_pt * 0.75)
    line0p75.SetLineWidth(2)
    # line0p75.Draw()

    line0p5 = ROOT.TLine(0, 0, max_pt, max_pt * 0.5)
    line0p5.SetLineWidth(2)
    # line0p5.Draw()

    c.SaveAs("%s/h2d_gen_l1_%g_%g%s.%s" % (oDir, eta_min, eta_max, app, oFormat))


def plot_rsp_Vs_l1(check_file, eta_min, eta_max, normX, logZ, oDir, oFormat="pdf"):
    """Plot response (l1/ref) Vs l1 pt"""
    app = "_normX" if normX else ""
    hname = "eta_%g_%g/Histograms/h2d_rsp_l1%s" % (eta_min, eta_max, app)
    fwd_bin = abs(eta_min)>2.9
    if cu.exists_in_file(check_file, hname):
        h2d_rsp_l1_orig = cu.get_from_file(check_file, hname)
    else:
        h2d_rsp_l1_orig = cu.get_from_file(check_file, "eta_%g_%g/Histograms/h2d_rsp_l1" % (eta_min, eta_max))
    if normX:
        h2d_rsp_l1_orig = cu.norm_vertical_bins(h2d_rsp_l1_orig, rescale_peaks=True)
    h2d_rsp_l1 = h2d_rsp_l1_orig.Rebin2D(2, 1, "hnew")
    c = generate_canvas()
    if logZ:
        c.SetLogz()
        app += "_log"
    h2d_rsp_l1.SetTitle("%s: %g-%g;%s;%s" % (eta_l1_str, eta_min, eta_max, pt_l1_str, rsp_str))
    if normX:
        h2d_rsp_l1.Draw("COL")
    else:
        h2d_rsp_l1.Draw("COLZ")
    h2d_rsp_l1.SetAxisRange(rsp_min, rsp_max, 'Y')
    if fwd_bin:
        h2d_rsp_l1.SetAxisRange(0, 254, 'X')
    line = ROOT.TLine(0, 1, 1022, 1)
    line.SetLineStyle(2)
    line.SetLineWidth(2)
    line.Draw()
    c.SaveAs("%s/h2d_rsp_l1_%g_%g%s.%s" % (oDir, eta_min, eta_max, app, oFormat))


def plot_rsp_Vs_ref(check_file, eta_min, eta_max, normX, logZ, oDir, oFormat="pdf"):
    """Plot response (l1/ref) Vs ref pt"""
    app = "_normX" if normX else ""
    hname = "eta_%g_%g/Histograms/h2d_rsp_gen%s" % (eta_min, eta_max, app)
    fwd_bin = abs(eta_min)>2.9
    if cu.exists_in_file(check_file, hname):
        h2d_rsp_ref_orig = cu.get_from_file(check_file, hname)
    else:
        h2d_rsp_ref_orig = cu.get_from_file(check_file, "eta_%g_%g/Histograms/h2d_rsp_gen" % (eta_min, eta_max))
    if normX:
        h2d_rsp_ref_orig = cu.norm_vertical_bins(h2d_rsp_ref_orig, rescale_peaks=True)
    h2d_rsp_ref = h2d_rsp_ref_orig.Rebin2D(2, 1, "hnew")
    c = generate_canvas()
    if logZ:
        c.SetLogz()
        app += "_log"
    h2d_rsp_ref.SetTitle("%s: %g-%g;%s;%s" % (eta_l1_str, eta_min, eta_max, pt_ref_str, rsp_str))
    if normX:
        h2d_rsp_ref.Draw("COL")
    else:
        h2d_rsp_ref.Draw("COLZ")
    h2d_rsp_ref.SetAxisRange(rsp_min, rsp_max, 'Y')
    if fwd_bin:
        h2d_rsp_ref.SetAxisRange(0, 254, 'X')
    line = ROOT.TLine(0, 1, 1022, 1)
    line.SetLineStyle(2)
    line.SetLineWidth(2)
    line.Draw()
    c.SaveAs("%s/h2d_rsp_ref_%g_%g%s.%s" % (oDir, eta_min, eta_max, app, oFormat))


def plot_rsp_Vs_pt_candle_violin(check_file, eta_min, eta_max, ptVar, oDir, oFormat):
    """Plot response vs pt as a candle plot and violin plot.
    Also puts fitted peak graph on there as well for comparison."""

    hname = "eta_%g_%g/Histograms/h2d_rsp_%s" % (eta_min, eta_max, ptVar)
    if cu.exists_in_file(check_file, hname):
        h2d_rsp_pt_orig = cu.get_from_file(check_file, hname)
    else:
        h2d_rsp_pt_orig = cu.get_from_file(check_file, "eta_%g_%g/Histograms/h2d_rsp_%s" % (eta_min, eta_max, ptVar))
    h2d_rsp_pt = h2d_rsp_pt_orig.Rebin2D(1, 1, "hnew")

    c = generate_canvas()
    h2d_rsp_pt.SetTitle("%s: %g-%g;%s;%s" % (eta_l1_str, eta_min, eta_max, pt_ref_str, rsp_str))
    h2d_rsp_pt.Draw("CANDLE")
    # Draw fitted peaks as well
    gr_name = "eta_{0:g}_{1:g}/gr_rsp_{2}_eta_{0:g}_{1:g}".format(eta_min, eta_max, 'pt' if ptVar == 'l1' else 'ptRef')
    gr = cu.get_from_file(check_file, gr_name)
    gr.SetLineColor(ROOT.kRed)
    gr.SetMarkerColor(ROOT.kRed)
    gr.SetMarkerStyle(21)
    gr.Draw("LP")

    max_pt = 100
    gr.GetXaxis().SetLimits(0, max_pt)
    h2d_rsp_pt.SetAxisRange(0, max_pt, 'X')
    h2d_rsp_pt.SetAxisRange(rsp_min, rsp_max, 'Y')

    line = ROOT.TLine(0, 1, max_pt, 1)
    line.SetLineStyle(2)
    line.SetLineWidth(2)
    line.Draw()
    c.SaveAs("%s/h2d_rsp_%s_%g_%g_box.%s" % (oDir, 'l1' if ptVar == 'l1' else 'ref', eta_min, eta_max, oFormat))

    h2d_rsp_pt.Draw("VIOLIN")
    gr.Draw("LP")
    c.SaveAs("%s/h2d_rsp_%s_%g_%g_violin.%s" % (oDir, 'l1' if ptVar == 'l1' else 'ref', eta_min, eta_max, oFormat))

def plot_rsp_eta_inclusive_graph(check_file, eta_min, eta_max, pt_var, oDir, oFormat="pdf"):
    """Plot a graph of response vs L1 eta."""
    grname = "eta_%g_%g/gr_rsp_%s_eta_%g_%g" % (eta_min, eta_max, pt_var, eta_min, eta_max)

    graph = cu.get_from_file(check_file, grname)

    c = generate_canvas(plot_title)

    # leg = generate_legend() #(0.4, 0.7, 0.87, 0.87) # top right
    # leg = generate_legend()

    mg = ROOT.TMultiGraph()

    i = 0
    graph.SetLineColor(plot_colors[i])
    graph.SetMarkerColor(plot_colors[i])
    graph.SetMarkerStyle(plot_markers[i])
    mg.Add(graph)
    # leg.AddEntry(graph, plot_labels[i], "LP")

    # lines at 1, and +/- 0.1
    line_central = ROOT.TLine(eta_min, 1, eta_max, 1)
    line_plus = ROOT.TLine(eta_min, 1.1, eta_max, 1.1)
    line_minus = ROOT.TLine(eta_min, 0.9, eta_max, 0.9)
    line_central.SetLineWidth(2)
    line_central.SetLineStyle(2)
    for line in [line_plus, line_minus]:
        line.SetLineWidth(2)
        line.SetLineStyle(3)

    # bundle all graphs into a TMultiGraph - set axes limits here
    mg.Draw("ALP")
    mg.GetYaxis().SetRangeUser(rsp_min, rsp_max)
    mg.GetXaxis().SetLimits(eta_min, eta_max)
    mg.GetXaxis().SetTitleSize(0.04)
    mg.GetXaxis().SetTitleOffset(0.9)
    # mg.GetYaxis().SetTitleSize(0.04)
    mg.Draw("ALP")
    mg.GetHistogram().SetTitle("%s;%s;%s" % (plot_title, eta_l1_str, rsp_str))

    # leg.Draw()
    [line.Draw() for line in [line_central, line_plus, line_minus]]
    append = ""
    c.SaveAs("%s/gr_rsp_eta_%g_%g%s.%s" % (oDir, eta_min, eta_max, append, oFormat))


def plot_rsp_eta_exclusive_graph(check_file, eta_min, eta_max, pt_bins, pt_var, oDir, oFormat="pdf"):
    """Plot a graph of response vs L1 eta.

    pt_bins is a list of pt bin edges to plot on the same graph
    pt_var is the varaible (pt or ptRef)
    """
    mg = ROOT.TMultiGraph()
    leg = generate_legend(x1=0.65, y1=0.65)
    c = generate_canvas(plot_title)
    gr_name = "eta_%g_%g/gr_rsp_eta_%g_%g_{0}_{1}_{2}" % (eta_min, eta_max, eta_min, eta_max)
    for i, (pt_min, pt_max) in enumerate(pt_bins):
        g = cu.get_from_file(check_file, gr_name.format(pt_var, pt_min, pt_max))
        g.SetLineColor(binning.eta_bin_colors[i])
        g.SetMarkerColor(binning.eta_bin_colors[i])
        g.SetMarkerStyle(plot_markers[0])
        mg.Add(g)
        # leg.AddEntry(g, plot_labels[0] + " %g < %s < %g" % (pt_min, pt_var, pt_max), "LP")
        leg.AddEntry(g, " %g < %s < %g" % (pt_min, pt_var, pt_max), "LP")

    # lines at 1, and +/- 0.1
    line_central = ROOT.TLine(eta_min, 1, eta_max, 1)
    line_plus = ROOT.TLine(eta_min, 1.1, eta_max, 1.1)
    line_minus = ROOT.TLine(eta_min, 0.9, eta_max, 0.9)
    line_central.SetLineWidth(2)
    line_central.SetLineStyle(2)
    for line in [line_plus, line_minus]:
        line.SetLineWidth(2)
        line.SetLineStyle(3)

    # bundle all graphs into a TMultiGraph - set axes limits here
    mg.Draw("ALP")
    mg.GetYaxis().SetRangeUser(rsp_min, rsp_max)
    mg.GetXaxis().SetLimits(eta_min, eta_max)
    mg.GetXaxis().SetTitleSize(0.04)
    mg.GetXaxis().SetTitleOffset(0.9)
    # mg.GetYaxis().SetTitleSize(0.04)
    mg.Draw("ALP")
    mg.GetHistogram().SetTitle("%s;%s;%s" % (plot_title, eta_l1_str, rsp_str))

    leg.Draw()
    [line.Draw() for line in [line_central, line_plus, line_minus]]
    c.SaveAs("%s/gr_rsp_eta_%g_%g_%s_%g_%g_binned.%s" % (oDir, eta_min, eta_max, pt_var, pt_bins[0][0], pt_bins[-1][1], oFormat))


def plot_rsp_pt_hists(check_file, eta_min, eta_max, pt_bins, pt_var, oDir, oFormat='pdf'):
    """Plot component hists of response vs pt graph, for given eta bin"""

    sub_dir = "eta_%g_%g" % (eta_min, eta_max)
    if not os.path.isdir("%s/%s" % (oDir, sub_dir)):
        os.mkdir("%s/%s" % (oDir, sub_dir))

    c = generate_canvas(plot_title)
    filenames = []
    for i, pt_min in enumerate(pt_bins[:-1]):
        pt_max = pt_bins[i + 1]
        hname = "%s/Histograms/rsp_%s_%g_%g" % (sub_dir, pt_var, pt_min, pt_max)
        try:
            hist = cu.get_from_file(check_file, hname)
            hist.SetTitle("%s;%s;N" % (plot_title, rsp_str))
            hist.Draw()
            filename = "%s/%s/rsp_%s_%g_%g.%s" % (oDir, sub_dir, pt_var, pt_min, pt_max, oFormat)
            c.SaveAs(filename)
            filenames.append(filename)
        except Exception:
            print '! No histogram %s exists' % hname
    return filenames


def plot_rsp_pt_graph(check_file, eta_min, eta_max, oDir, oFormat='pdf'):
    """Plot a graph of response vs pt (L1) for a given eta bin"""

    grname = "eta_%g_%g/gr_rsp_pt_eta_%g_%g" % (eta_min, eta_max, eta_min, eta_max)

    graph = cu.get_from_file(check_file, grname)

    c = generate_canvas(plot_title)

    # leg = generate_legend()

    mg = ROOT.TMultiGraph()

    i = 0
    graph.SetLineColor(plot_colors[i])
    graph.SetMarkerColor(plot_colors[i])
    graph.SetMarkerStyle(plot_markers[i])
    mg.Add(graph)
    # leg.AddEntry(graph, plot_labels[i], "LP")

    pt_min, pt_max = 0, 1022
    # lines at 1, and +/- 0.1
    line_central = ROOT.TLine(pt_min, 1, pt_max, 1)
    line_plus = ROOT.TLine(pt_min, 1.1, pt_max, 1.1)
    line_minus = ROOT.TLine(pt_min, 0.9, pt_max, 0.9)
    line_central.SetLineWidth(2)
    line_central.SetLineStyle(2)
    for line in [line_plus, line_minus]:
        line.SetLineWidth(2)
        line.SetLineStyle(3)

    # bundle all graphs into a TMultiGraph - set axes limits here
    mg.Draw("ALP")
    mg.GetYaxis().SetRangeUser(rsp_min, rsp_max)
    mg.GetXaxis().SetLimits(pt_min, pt_max)
    mg.GetXaxis().SetTitleSize(0.04)
    mg.GetXaxis().SetTitleOffset(0.9)
    # mg.GetYaxis().SetTitleSize(0.04)
    mg.Draw("ALP")
    mg.GetHistogram().SetTitle("%s;%s;%s" % (plot_title + ", %g < %s < %g" % (eta_min, eta_l1_str, eta_max), pt_l1_str, rsp_str))

    # leg.Draw()
    [line.Draw() for line in [line_central, line_plus, line_minus]]
    append = ""
    c.SaveAs("%s/gr_rsp_pt_eta_%g_%g%s.%s" % (oDir, eta_min, eta_max, append, oFormat))


def plot_rsp_ptRef_graph(check_file, eta_min, eta_max, oDir, oFormat='pdf'):
    """Plot a graph of response vs pt (L1) for a given eta bin"""

    grname = "eta_%g_%g/gr_rsp_ptRef_eta_%g_%g" % (eta_min, eta_max, eta_min, eta_max)

    c = generate_canvas(plot_title)

    # leg = generate_legend()

    mg = ROOT.TMultiGraph()

    i = 0
    graph = cu.get_from_file(check_file, grname)
    graph.SetLineColor(plot_colors[i])
    graph.SetMarkerColor(plot_colors[i])
    graph.SetMarkerStyle(plot_markers[i])
    mg.Add(graph)
    # leg.AddEntry(graph, plot_labels[i], "LP")

    pt_min, pt_max = 0, 1022
    # lines at 1, and +/- 0.1
    line_central = ROOT.TLine(pt_min, 1, pt_max, 1)
    line_plus = ROOT.TLine(pt_min, 1.1, pt_max, 1.1)
    line_minus = ROOT.TLine(pt_min, 0.9, pt_max, 0.9)
    line_central.SetLineWidth(2)
    line_central.SetLineStyle(2)
    for line in [line_plus, line_minus]:
        line.SetLineWidth(2)
        line.SetLineStyle(3)

    # bundle all graphs into a TMultiGraph - set axes limits here
    mg.Draw("ALP")
    mg.GetYaxis().SetRangeUser(rsp_min, 2)
    mg.GetXaxis().SetLimits(pt_min, pt_max)
    mg.GetXaxis().SetTitleSize(0.04)
    mg.GetXaxis().SetTitleOffset(0.9)
    # mg.GetYaxis().SetTitleSize(0.04)
    mg.Draw("ALP")
    mg.GetHistogram().SetTitle("%s;%s;%s" % (plot_title + ", %g < %s < %g" % (eta_min, eta_l1_str, eta_max), pt_ref_str, rsp_str))

    # leg.Draw()
    [line.Draw() for line in [line_central, line_plus, line_minus]]
    append = ""
    c.SaveAs("%s/gr_rsp_ptRef_eta_%g_%g%s.%s" % (oDir, eta_min, eta_max, append, oFormat))


def plot_rsp_pt_binned_graph(check_file, eta_bins, pt_var, oDir, oFormat='pdf', x_range=None):
    """Plot a graph of response vs pt_var, in bins of eta"""

    mg = ROOT.TMultiGraph()
    leg = generate_legend(x1=0.65, y1=0.65)
    c = generate_canvas(plot_title)
    gr_name = "eta_{0:g}_{1:g}/gr_rsp_%s_eta_{0:g}_{1:g}" % (pt_var)
    for i, (eta_min, eta_max) in enumerate(zip(eta_bins[:-1], eta_bins[1:])):
        g = cu.get_from_file(check_file, gr_name.format(eta_min, eta_max))
        g.SetLineColor(binning.eta_bin_colors[i])
        g.SetMarkerColor(binning.eta_bin_colors[i])
        g.SetMarkerStyle(plot_markers[0])
        mg.Add(g)
        # leg.AddEntry(g, plot_labels[0] + " %g < |#eta^{L1}| < %g" % (eta_min, eta_var), "LP")
        leg.AddEntry(g, " %g < %s < %g" % (eta_min, eta_l1_str, eta_max), "LP")

    pt_min, pt_max = (0, 1022) if not x_range else (x_range[0], x_range[1])
    # lines at 1, and +/- 0.1
    line_central = ROOT.TLine(pt_min, 1, pt_max, 1)
    line_plus = ROOT.TLine(pt_min, 1.1, pt_max, 1.1)
    line_minus = ROOT.TLine(pt_min, 0.9, pt_max, 0.9)
    line_central.SetLineWidth(2)
    line_central.SetLineStyle(2)
    for line in [line_plus, line_minus]:
        line.SetLineWidth(2)
        line.SetLineStyle(3)

    # bundle all graphs into a TMultiGraph - set axes limits here
    mg.Draw("ALP")
    mg.GetYaxis().SetRangeUser(rsp_min, rsp_max)
    mg.GetXaxis().SetLimits(pt_min, pt_max)
    mg.GetXaxis().SetTitleSize(0.04)
    mg.GetXaxis().SetTitleOffset(0.9)
    # mg.GetYaxis().SetTitleSize(0.04)
    mg.Draw("ALP")
    xtitle = pt_l1_str if pt_var == "pt" else pt_ref_str
    mg.GetHistogram().SetTitle("%s;%s;%s" % (plot_title, xtitle, rsp_str))

    leg.Draw()
    [line.Draw() for line in [line_central, line_plus, line_minus]]
    c.SaveAs("%s/gr_rsp_%s_eta_%g_%g_binned.%s" % (oDir, pt_var, eta_bins[0], eta_bins[-1], oFormat))


#############################################
# PLOTS USING OUTPUT FROM runCalibration
#############################################
def plot_correction_graph(calib_file, eta_min, eta_max, oDir, oFormat='pdf'):
    """Plot the graph of correction value vs pT"""
    gname = generate_eta_graph_name(eta_min, eta_max)
    gr = cu.get_from_file(calib_file, gname)
    c = generate_canvas()
    gr.Draw("ALP")
    y_min = ROOT.TMath.MinElement(gr.GetN(), gr.GetY())
    y_max = ROOT.TMath.MaxElement(gr.GetN(), gr.GetY())
    if y_max > 5:
        y_max = 5
    gr.GetYaxis().SetRangeUser(y_min * 0.7, y_max * 1.1)
    c.SaveAs('%s/%s.%s' % (oDir, gname, oFormat))


def plot_rsp_eta_pt_bin(calib_file, eta_min, eta_max, pt_min, pt_max, oDir, oFormat="pdf"):
    """Plot the response in one pt, eta bin"""
    sub_dir = "eta_%g_%g" % (eta_min, eta_max)
    if not os.path.isdir("%s/%s" % (oDir, sub_dir)):
        os.mkdir("%s/%s" % (oDir, sub_dir))
    hname = "eta_%g_%g/Histograms/Rsp_genpt_%g_%g" % (eta_min, eta_max, pt_min, pt_max)
    # ignore histogram not found errors... naughty naughty
    try:
        h_rsp = cu.get_from_file(calib_file, hname)
        c = generate_canvas()
        h_rsp.Draw("HISTE")
        func = h_rsp.GetListOfFunctions().At(0)
        if func:
            func.Draw("SAME")
        h_rsp.SetTitle("%s;%s;" % (hname, rsp_str))
        filepath = "%s/%s/h_rsp_%g_%g_%g_%g.%s" % (oDir, sub_dir, eta_min, eta_max, pt_min, pt_max, oFormat)
        c.SaveAs(filepath)
        return filepath
    except Exception:
        print "! No histogram %s exists" % hname


def plot_pt_bin(calib_file, eta_min, eta_max, pt_min, pt_max, oDir, oFormat="pdf"):
    """Plot the L1 pt in a given ref jet pt bin, for a given eta bin"""
    sub_dir = "eta_%g_%g" % (eta_min, eta_max)
    if not os.path.isdir("%s/%s" % (oDir, sub_dir)):
        os.mkdir("%s/%s" % (oDir, sub_dir))
    hname = "eta_%g_%g/Histograms/L1_pt_genpt_%g_%g" % (eta_min, eta_max, pt_min, pt_max)
    # ignore histogram not found errors... naughty naughty
    try:
        h_pt = cu.get_from_file(calib_file, hname)
        c = generate_canvas()
        h_pt.Draw("HISTE")
        filepath = "%s/%s/L1_pt_%g_%g_%g_%g.%s" % (oDir, sub_dir, eta_min, eta_max, pt_min, pt_max, oFormat)
        c.SaveAs(filepath)
        return filepath
    except Exception:
        print "! No histogram %s exists" % hname


##################
# Helper functions
##################
def write_filelist(plot_filenames, list_file):
    """Write a list of plot filenames to a text file."""
    if plot_filenames:
        with open(list_file, 'w') as f:
            f.write('\n'.join(map(lambda x: os.path.basename(x), filter(None, plot_filenames))))
    else:
        print 'Warning: nothing to write to txt file'


def make_gif(input_file_list, output_gif_filename, convert_exe):
    """Make an animated GIF from a list of images.
    Requires Imagemagick to be installed.

    Does a preliminary check to ensure that the input filelist is not empty,
    otherwise convert will error.

    Note that we cd to the directory with the input file list, as all image
    files are assumed to be relative to its location.

    Parameters
    ----------
    input_file_list : str
        Filepath of txt file with locations of images to be made into GIF
    output_gif_filename : str
        Filepath of GIF
    """
    print 'Making GIF', output_gif_filename, 'from', input_file_list
    input_file_list = os.path.abspath(input_file_list)

    if not os.path.isfile(input_file_list):
        print 'Skipping GIF making as %s does not exist' % input_file_list
        return

    if os.stat(input_file_list).st_size == 0:
        print 'Skipping GIF making as %s is empty' % input_file_list
        return

    output_gif_filename = os.path.abspath(output_gif_filename)
    cwd = os.getcwd()
    # we have to chdir since list file only has bare filenames
    os.chdir(os.path.dirname(input_file_list))
    cmd = "%s -dispose Background -delay 50 -loop 0 @%s %s" % (convert_exe, os.path.relpath(input_file_list), os.path.relpath(output_gif_filename))
    print cmd
    check_output(cmd.split())
    os.chdir(cwd)


def main(in_args=sys.argv[1:]):
    print in_args
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--pairs",
                        help="input ROOT file with matched pairs from RunMatcher")

    parser.add_argument("--res",
                        help="input ROOT file with resolution plots from makeResolutionPlots.py")

    parser.add_argument("--checkcal",
                        help="input ROOT file with calibration check plots from checkCalibration.py")

    parser.add_argument("--calib",
                        help="input ROOT file from output of runCalibration.py")

    parser.add_argument("--oDir",
                        help="Directory to save plots. Default is in same location as ROOT file.")
    parser.add_argument("--detail",
                        help="Plot all the individual component hists for each eta bin. There are a lot!",
                        action='store_true')
    parser.add_argument("--format",
                        help="Format for plots (PDF, png, etc). Note that 2D correlation plots will "
                             "always be PNGs to avoid large files.",
                        default="pdf")
    parser.add_argument("--title",
                        help="Title for plots.")
    parser.add_argument('--zip',
                        help="Zip filename for zipping up all plots. Don't include extension")

    # FIXME
    # parser.add_argument("--etaInd",
                        # help="list of eta bin index/indices to run over")
    parser.add_argument("--gifs",
                        help="Make GIFs (only applicable if --detail is also used)",
                        action='store_true')
    parser.add_argument("--gifexe",
                        help='Convert executable to use. Default is result of `which convert`')
    args = parser.parse_args(args=in_args)

    print args

    if args.detail:
        print "Warning: producing all component hists. This could take a while..."

    if args.gifs:
        if args.detail:
            print "Making animated graphs from fit plots."
        else:
            print "To use the --gifs flag, you also need --detail"

    if not args.gifexe:
        args.gifexe = find_executable('convert')
        if not args.gifexe:
            print 'Cannot find convert exe, not making gifs'
            args.gif = False
        else:
            print 'Using %s to make GIFs' % args.gifexe

    # customise titles
    # note the use of global keyword
    if args.title:
        global plot_title
        plot_title = args.title

    if args.oDir == os.getcwd():
        print "Warning: plots will be made in $PWD!"

    # auto determine output directory
    if not args.oDir:
        filename, stem = '', ''
        if args.pairs:
            filename, stem = args.pairs, 'pairs_'
        elif args.checkcal:
            filename, stem = args.checkcal, 'check_'
        elif args.res:
            filename, stem = args.res, 'res_'
        elif args.calib:
            filename, stem = args.calib, 'output_'
        new_dir = os.path.basename(filename).replace(".root", '').replace(stem, 'showoff_')

        args.oDir = os.path.join(os.path.dirname(os.path.abspath(filename)), new_dir)

    cu.check_dir_exists_create(args.oDir)
    print "Output directory:", args.oDir


    # Choose eta
    ptBins = binning.pt_bins_stage2

    # Do plots with output from RunMatcher
    # ------------------------------------------------------------------------
    if args.pairs:
        pairs_file = cu.open_root_file(args.pairs)
        pairs_tree = cu.get_from_file(pairs_file, "valid")

        # eta binned
        for emin, emax in pairwise(binning.eta_bins):
            plot_dR(pairs_tree, eta_min=emin, eta_max=emax, cut="1", oDir=args.oDir)
            plot_pt_both(pairs_tree, eta_min=emin, eta_max=emax, cut="1", oDir=args.oDir)

        # plot_dR(pairs_tree, eta_min=0, eta_max=5, cut="1", oDir=args.oDir)  # all eta
        # plot_pt_both(pairs_tree, eta_min=0, eta_max=5, cut="1", oDir=args.oDir)  # all eta
        plot_eta_both(pairs_tree, oDir=args.oDir)  # all eta

        plot_dR(pairs_tree, eta_min=0, eta_max=3, cut="1", oDir=args.oDir)  # central
        plot_pt_both(pairs_tree, eta_min=0, eta_max=3, cut="1", oDir=args.oDir)  # central

        plot_dR(pairs_tree, eta_min=3, eta_max=5, cut="1", oDir=args.oDir)  # forward
        plot_pt_both(pairs_tree, eta_min=3, eta_max=5, cut="1", oDir=args.oDir)  # forward

        pairs_file.Close()

    # Do plots with output from makeResolutionPlots.py
    # ------------------------------------------------------------------------
    if args.res:
        res_file = cu.open_root_file(args.res)
        # pt_min = binning.pt_bins[10]
        # pt_max = binning.pt_bins[11]
        # for the first 4 bins - troublesome

        # exclusive eta graphs
        # for emin, emax in izip(binning.eta_bins[:-1], binning.eta_bins[1:]):
            # plot_res_all_pt([res_file], emin, emax, args.oDir, args.format)
            # for pt_min, pt_max in izip(binning.pt_bins[4:-1], binning.pt_bins[5:]):
            #     plot_pt_diff(res_file, emin, emax, pt_min, pt_max, args.oDir, args.format)
            # plot_res_pt_bin(res_file, eta_min, eta_max, pt_min, pt_max, args.oDir, args.format)

        # inclusive eta graphs
        for (eta_min, eta_max) in [[0, 3], [3, 5]]:
            plot_res_all_pt(res_file, eta_min, eta_max, args.oDir, args.format)
            plot_ptDiff_Vs_pt(res_file, eta_min, eta_max, args.oDir, args.format)

        # plot_eta_pt_rsp_2d(res_file, binning.eta_bins, binning.pt_bins[4:], args.oDir, args.format)

        # components of these:
        for pt_min, pt_max in izip(binning.pt_bins[4:-1], binning.pt_bins[5:]):
            plot_pt_diff(res_file, 0, 3, pt_min, pt_max, args.oDir, args.format)
            # plot_pt_diff(res_file, 0, 5, pt_min, pt_max, args.oDir, args.format)
            # plot_pt_diff(res_file, 3, 5, pt_min, pt_max, args.oDir, args.format)

        res_file.Close()

    # Do plots with output from checkCalibration.py
    # ------------------------------------------------------------------------
    if args.checkcal:

        etaBins = binning.eta_bins
        check_file = cu.open_root_file(args.checkcal)

        # ptBinsWide = list(np.arange(10, 250, 8))

        # indiviudal eta bins
        for eta_min, eta_max in pairwise(etaBins):
            for (normX, logZ) in product([True, False], [True, False]):
                plot_l1_Vs_ref(check_file, eta_min, eta_max, logZ, args.oDir, 'png')
                plot_rsp_Vs_l1(check_file, eta_min, eta_max, normX, logZ, args.oDir, 'png')
                plot_rsp_Vs_ref(check_file, eta_min, eta_max, normX, logZ, args.oDir, 'png')
                plot_rsp_Vs_pt_candle_violin(check_file, eta_min, eta_max, "l1", args.oDir, 'png')
                plot_rsp_Vs_pt_candle_violin(check_file, eta_min, eta_max, "gen", args.oDir, 'png')

            if args.detail:
                list_dir = os.path.join(args.oDir, 'eta_%g_%g' % (eta_min, eta_max))
                cu.check_dir_exists_create(list_dir)

                # print individual histograms, and make a list suitable for imagemagick to turn into a GIF
                pt_plot_filenames = plot_rsp_pt_hists(check_file, eta_min, eta_max, ptBins, "pt", args.oDir, 'png')
                pt_plot_filenames_file = os.path.join(list_dir, 'list_pt.txt')
                write_filelist(pt_plot_filenames, pt_plot_filenames_file)

                # print individual histograms, and make a list suitable for imagemagick to turn into a GIF
                ptRef_plot_filenames = plot_rsp_pt_hists(check_file, eta_min, eta_max, ptBins, "ptRef", args.oDir, 'png')
                ptRef_plot_filenames_file = os.path.join(list_dir, 'list_ptRef.txt')
                write_filelist(ptRef_plot_filenames, ptRef_plot_filenames_file)

                # make dem GIFs
                if args.gifs:
                    for inf in [pt_plot_filenames_file, ptRef_plot_filenames_file]:
                        make_gif(inf, inf.replace('.txt', '.gif'), args.gifexe)
                else:
                    print "To make animated gif from PNGs using a plot list:"
                    print "convert -dispose Background -delay 50 -loop 0 @%s " \
                        "%s" % (pt_plot_filenames_file,
                                os.path.basename(pt_plot_filenames_file).replace(".txt", ".gif"))

        # Graph of response vs pt, but in bins of eta
        x_range = [0, 150]  # for zoomed-in low pt
        x_range = None
        plot_rsp_pt_binned_graph(check_file, etaBins, "pt", args.oDir, args.format, x_range=x_range)
        plot_rsp_pt_binned_graph(check_file, etaBins, "ptRef", args.oDir, args.format, x_range=x_range)

        all_rsp_pt_plot_filenames = []
        all_rsp_ptRef_plot_filenames = []

        # Loop over central/forward eta, do 2D plots, and graphs, and component hists
        # ALSO EDITED THE MIN AND MAX ETAS HERE
        for (eta_min, eta_max) in [[0, 2.964], [2.964, 5.191]]:
            print eta_min, eta_max

            for (normX, logZ) in product([True, False], [True, False]):
                plot_l1_Vs_ref(check_file, eta_min, eta_max, logZ, args.oDir, 'png')
                plot_rsp_Vs_l1(check_file, eta_min, eta_max, normX, logZ, args.oDir, 'png')
                plot_rsp_Vs_ref(check_file, eta_min, eta_max, normX, logZ, args.oDir, 'png')

            if args.detail:
                plot_rsp_pt_hists(check_file, eta_min, eta_max, ptBins, "pt", args.oDir, 'png')
                plot_rsp_pt_hists(check_file, eta_min, eta_max, ptBins, "ptRef", args.oDir, 'png')

            # graphs
            plot_rsp_eta_inclusive_graph(check_file, eta_min, eta_max, 'pt', args.oDir, args.format)
            plot_rsp_eta_inclusive_graph(check_file, eta_min, eta_max, 'ptRef', args.oDir, args.format)
            plot_rsp_eta_exclusive_graph(check_file, eta_min, eta_max, binning.check_pt_bins, 'pt', args.oDir, args.format)
            plot_rsp_eta_exclusive_graph(check_file, eta_min, eta_max, binning.check_pt_bins, 'ptRef', args.oDir, args.format)

            plot_rsp_pt_graph(check_file, eta_min, eta_max, args.oDir, args.format)
            plot_rsp_ptRef_graph(check_file, eta_min, eta_max, args.oDir, args.format)

            for etamin, etamax in pairwise(etaBins):
                if etamin < eta_min or etamax > eta_max:
                    continue
                print etamin, etamax
                this_rsp_pt_plot_filenames = []
                this_rsp_ptRef_plot_filenames = []
                # component hists/fits for the eta graphs, binned by pt
                for pt_min, pt_max in binning.check_pt_bins:
                    pt_filename = plot_rsp_eta_bin_pt(check_file, etamin, etamax, 'pt', pt_min, pt_max, args.oDir, 'png')
                    if pt_filename:
                        this_rsp_pt_plot_filenames.append(pt_filename)
                    ptRef_filename = plot_rsp_eta_bin_pt(check_file, etamin, etamax, 'ptRef', pt_min, pt_max, args.oDir, 'png')
                    if ptRef_filename:
                        this_rsp_ptRef_plot_filenames.append(ptRef_filename)

                pt_list_file = os.path.join(args.oDir, 'list_pt_eta_%g_%g.txt' % (etamin, etamax))
                write_filelist(this_rsp_pt_plot_filenames, pt_list_file)
                if args.gifs:
                    make_gif(pt_list_file, pt_list_file.replace('.txt', '.gif'), args.gifexe)

                ptRef_list_file = os.path.join(args.oDir, 'list_ptRef_eta_%g_%g.txt' % (etamin, etamax))
                write_filelist(this_rsp_ptRef_plot_filenames, ptRef_list_file)
                if args.gifs:
                    make_gif(ptRef_list_file, ptRef_list_file.replace('.txt', '.gif'), args.gifexe)

                all_rsp_pt_plot_filenames.extend(this_rsp_pt_plot_filenames)
                all_rsp_ptRef_plot_filenames.extend(this_rsp_ptRef_plot_filenames)

        pt_list_file = os.path.join(args.oDir, 'list_pt_eta_%g_%g.txt' % (etaBins[0], etaBins[-1]))
        write_filelist(all_rsp_pt_plot_filenames, pt_list_file)
        if args.gifs:
            make_gif(pt_list_file, pt_list_file.replace('.txt', '.gif'), args.gifexe)

        ptRef_list_file = os.path.join(args.oDir, 'list_ptRef_eta_%g_%g.txt' % (etaBins[0], etaBins[-1]))
        write_filelist(all_rsp_ptRef_plot_filenames, ptRef_list_file)
        if args.gifs:
            make_gif(ptRef_list_file, ptRef_list_file.replace('.txt', '.gif'), args.gifexe)

        check_file.Close()

    # Do plots with output from runCalibration.py
    # ------------------------------------------------------------------------
    if args.calib:

        calib_file = cu.open_root_file(args.calib)

        for eta_min, eta_max in pairwise(binning.eta_bins):

            print eta_min, eta_max

            # 2D correlation heat maps
            for (normX, logZ) in product([True, False], [True, False]):
                plot_rsp_Vs_ref(calib_file, eta_min, eta_max, normX, logZ, args.oDir, 'png')
                plot_rsp_Vs_l1(calib_file, eta_min, eta_max, normX, logZ, args.oDir, 'png')

            # individual fit histograms for each pt bin
            if args.detail:

                list_dir = os.path.join(args.oDir, 'eta_%g_%g' % (eta_min, eta_max))
                cu.check_dir_exists_create(list_dir)

                if eta_min > 2.9:
                    ptBins = binning.pt_bins_stage2_hf

                rsp_plot_filenames = []
                pt_plot_filenames = []

                for pt_min, pt_max in pairwise(ptBins):
                    rsp_name = plot_rsp_eta_pt_bin(calib_file, eta_min, eta_max, pt_min, pt_max, args.oDir, 'png')
                    rsp_plot_filenames.append(rsp_name)
                    pt_name = plot_pt_bin(calib_file, eta_min, eta_max, pt_min, pt_max, args.oDir, 'png')
                    pt_plot_filenames.append(pt_name)

                # print individual histograms, and make a list suitable for imagemagick to turn into a GIF
                rsp_plot_filenames_file = os.path.join(list_dir, 'list_rsp.txt')
                write_filelist(rsp_plot_filenames, rsp_plot_filenames_file)

                # print individual histograms, and make a list suitable for imagemagick to turn into a GIF
                pt_plot_filenames_file = os.path.join(list_dir, 'list_pt.txt')
                write_filelist(pt_plot_filenames, pt_plot_filenames_file)

                # make dem gifs
                if args.gifs:
                    for inf in [pt_plot_filenames_file, rsp_plot_filenames_file]:
                        make_gif(inf, inf.replace('.txt', '.gif'), args.gifexe)
                else:
                    print "To make animated gif from PNGs using a plot list:"
                    print "convert -dispose Background -delay 50 -loop 0 @%s "\
                        "pt_eta_%g_%g.gif" % (pt_plot_filenames_file, eta_min, eta_max)

            # the correction curve graph
            plot_correction_graph(calib_file, eta_min, eta_max, args.oDir, args.format)

        calib_file.Close()

    if args.zip:
        print 'Zipping up files'
        zip_filename = os.path.basename(args.zip.split('.')[0])
        make_archive(zip_filename, 'gztar', args.oDir)


if __name__ == "__main__":
    main()
