#include "runMatcherUtils.h"

// STL headers
#include <iostream>
#include <utility>
#include <stdexcept>
#include <algorithm>

// ROOT headers
#include "TFile.h"
#include "TTree.h"
#include "TRegexp.h"

// BOOST headers
#include <boost/algorithm/string.hpp>
#include <boost/algorithm/string/predicate.hpp>
#include <boost/lexical_cast.hpp>

// Headers from this package
#include "commonRootUtils.h"

using boost::lexical_cast;

template<typename T>
std::vector<TLorentzVector> makeTLorentzVectors(std::vector<T> & et,
                                                std::vector<T> & eta,
                                                std::vector<T> & phi) {
    // check all same size
    if (et.size() != eta.size() || et.size() != phi.size()) {
        throw std::range_error("Et/eta/phi vectors different sizes, cannot make TLorentzVectors from sizes " +
                                lexical_cast<std::string>(et.size()) + "/" + lexical_cast<std::string>(eta.size()) +
                                "/" + lexical_cast<std::string>(phi.size()));
    }
    std::vector<TLorentzVector> vecs;
    for (unsigned i = 0; i < et.size(); i++) {
        TLorentzVector v;
        v.SetPtEtaPhiM(et.at(i), eta.at(i), phi.at(i), 0);
        vecs.push_back(v);
    }
    return vecs;
}
// need to explicity write down template implementations here, or put function implementation into header...
template std::vector<TLorentzVector> makeTLorentzVectors<float>(std::vector<float> & et, std::vector<float> & eta, std::vector<float> & phi);
template std::vector<TLorentzVector> makeTLorentzVectors<double>(std::vector<double> & et, std::vector<double> & eta, std::vector<double> & phi);


template<typename T, typename T2>
std::vector<TLorentzVector> makeTLorentzVectors(std::vector<T> & et,
                                                std::vector<T> & eta,
                                                std::vector<T> & phi,
                                                std::vector<T2> & bx) {
    // check all same size
    if (et.size() != eta.size() || et.size() != phi.size()) {
        throw std::range_error("Et/eta/phi vectors different sizes, cannot make TLorentzVectors from sizes " +
                                lexical_cast<std::string>(et.size()) + "/" + lexical_cast<std::string>(eta.size()) +
                                "/" + lexical_cast<std::string>(phi.size()));
    }
    std::vector<TLorentzVector> vecs;
    for (unsigned i = 0; i < et.size(); i++) {
        if (bx.at(i) == 0) {
            TLorentzVector v;
            v.SetPtEtaPhiM(et.at(i), eta.at(i), phi.at(i), 0);
            vecs.push_back(v);
        }
    }
    return vecs;
}
template std::vector<TLorentzVector> makeTLorentzVectors<float, short int>(std::vector<float> & et, std::vector<float> & eta, std::vector<float> & phi, std::vector<short int> & bx);
template std::vector<TLorentzVector> makeTLorentzVectors<float, int>(std::vector<float> & et, std::vector<float> & eta, std::vector<float> & phi, std::vector<int> & bx);
template std::vector<TLorentzVector> makeTLorentzVectors<double, int>(std::vector<double> & et, std::vector<double> & eta, std::vector<double> & phi, std::vector<int> & bx);


void loadCorrectionFunctions(const TString& filename,
                             std::vector<TF1>& corrFns,
                             const std::vector<float>& etaBins) {

    TFile * corrFile = openFile(filename, "READ");

    // Loop over eta bins
    for (unsigned ind = 0; ind < etaBins.size()-1; ++ind) {
        float etaMin(etaBins[ind]), etaMax(etaBins[ind+1]);
        TString binName = TString::Format("fitfcneta_%g_%g", etaMin, etaMax);
        TF1 * fit = dynamic_cast<TF1*>(corrFile->Get(binName));
        // Make a copy of function and store in vector
        if (fit) {
            TF1 fitFcn(*fit);
            corrFns.push_back(fitFcn);
        } else {
            // throw invalid_argument(binName.Prepend("No TF1 with name ").Data());
            // load in flat function if no suitable one is in file
            TF1 fitFcn(binName, "1");
            corrFns.push_back(fitFcn);
            cout << "No correction fn found for eta bin ";
            cout << etaMin << " - " << etaMax << endl;
            cout << ": Will not correct jets in this bin" << endl;
        }
    }
    corrFile->Close();
}


void correctJets(std::vector<TLorentzVector>& jets,
                 std::vector<TF1>& corrFns,
                 std::vector<float>& etaBins,
                 float minPt) {
    // NB to future self: tried to make corrFns and etaBins const,
    // but lower_bound doesn't like that

    // check corrFn correct size
    if (corrFns.size() != etaBins.size()-1) {
        throw std::range_error("Corrections functions don't match eta bins");
    }

    // Loop over jets, get correct function for given |eta| & apply if necessary
    for (auto& jetItr: jets) {
        // Get eta bin limits corresponding to jet |eta|
        float absEta = fabs(jetItr.Eta());
        auto maxItr = std::lower_bound(etaBins.begin(), etaBins.end(), absEta);
        if (maxItr == etaBins.begin()) {
            throw std::range_error("Max eta != first eta bin");
        }
        auto minItr = maxItr - 1;

        // Get correction fn for this bin
        TF1 corrFn = corrFns[minItr-etaBins.begin()];

        // Get fit range
        double fitMin(0.), fitMax(250.);
        corrFn.GetRange(fitMin, fitMax);

        // Now decide if we should apply corrections
        // Can either use range of fit function, or above some minimum pt
        // Might get rid of former option - get disjoint pt spectrum
        if (((minPt < 0.) && (jetItr.Pt() > fitMin) && (jetItr.Pt() < fitMax))
            || ((minPt >= 0.) && (jetItr.Pt() >= minPt))) {
            // corrFn.Print();
            float newPt = jetItr.Pt() * corrFn.Eval(jetItr.Pt());
            // safeguard against crazy values
            if (newPt < 1000. && newPt > 0.) {
                jetItr.SetPtEtaPhiM(newPt, jetItr.Eta(), jetItr.Phi(), jetItr.M());
            }
        }
    }
}


std::string getCurrentTime() {
    time_t now = time(0);
    char* dt = ctime(&now);
    std::string str1 = std::string(dt);
    boost::algorithm::trim(str1);
    return str1;
}


TString removePattern(const TString & str, const TString & pattern) {
    TString suffix(str);
    TRegexp re(pattern);
    // replace the substring matching the regex with ""
    suffix(re) = "";
    if (suffix == "") suffix = str;
    return suffix;
}


void rescaleEnergyFractions(L1AnalysisRecoJetDataFormat * jets) {
    for (unsigned i = 0; i < jets->nJets; ++i) {
        float totalEf = jets->chef[i] + jets->nhef[i] + jets->pef[i] + jets->eef[i] + jets->mef[i] + jets->hfhef[i] + jets->hfemef[i];
        jets->chef[i] /= totalEf;
        jets->nhef[i] /= totalEf;
        jets->pef[i] /= totalEf;
        jets->eef[i] /= totalEf;
        jets->mef[i] /= totalEf;
        jets->hfhef[i] /= totalEf;
        jets->hfemef[i] /= totalEf;
    }
}


std::vector<TLorentzVector> makeRecoTLorentzVectorsCleaned(const L1AnalysisRecoJetDataFormat & jets, std::string quality) {

    std::vector<TLorentzVector> vecs;

    for (unsigned i = 0; i < jets.nJets; ++i) {
        if (quality == "LOOSE") {
            if (!looseCleaning(jets.eta[i],
                               jets.chef[i], jets.nhef[i], jets.pef[i], jets.eef[i], jets.mef[i], jets.hfhef[i], jets.hfemef[i],
                               jets.chMult[i], jets.nhMult[i], jets.phMult[i], jets.elMult[i], jets.muMult[i], jets.hfhMult[i], jets.hfemMult[i]))
                continue;
        } else if (quality == "TIGHT") {
            if (!tightCleaning(jets.eta[i],
                               jets.chef[i], jets.nhef[i], jets.pef[i], jets.eef[i], jets.mef[i], jets.hfhef[i], jets.hfemef[i],
                               jets.chMult[i], jets.nhMult[i], jets.phMult[i], jets.elMult[i], jets.muMult[i], jets.hfhMult[i], jets.hfemMult[i]))
                continue;
        } else if (quality == "TIGHTLEPVETO") {
            if (!tightLepVetoCleaning(jets.eta[i],
                                      jets.chef[i], jets.nhef[i], jets.pef[i], jets.eef[i], jets.mef[i], jets.hfhef[i], jets.hfemef[i],
                                      jets.chMult[i], jets.nhMult[i], jets.phMult[i], jets.elMult[i], jets.muMult[i], jets.hfhMult[i], jets.hfemMult[i]))
                continue;
        } else {
            throw std::runtime_error("quality must be LOOSE/TIGHT/TIGHTLEPVETO");
        }
        // If got this far, then can add to list.
        TLorentzVector v;
        v.SetPtEtaPhiM(jets.etCorr[i], jets.eta[i], jets.phi[i], 0);
        vecs.push_back(v);
    }

    return vecs;
}


bool looseCleaning(float eta,
                   float chef, float nhef, float pef, float eef, float mef, float hfhef, float hfemef,
                   short chMult, short nhMult, short phMult, short elMult, short muMult, short hfhMult, short hfemMult) {
    if (fabs(eta) <= 3) {
        if ((fabs(eta) <= 2.4) && !((chef > 0) && ((chMult+elMult+muMult) > 0) && (eef < 0.99)))
            return false;
        return (nhef < 0.99) && (pef < 0.99) && ((chMult+nhMult+phMult+elMult+muMult) > 1);
    } else {
        return (pef < 0.9 && (nhMult + phMult) > 10);
    }
}


bool tightCleaning(float eta,
                   float chef, float nhef, float pef, float eef, float mef, float hfhef, float hfemef,
                   short chMult, short nhMult, short phMult, short elMult, short muMult, short hfhMult, short hfemMult) {
    if (fabs(eta) <= 3) {
        if ((fabs(eta) <= 2.4) && !((chef > 0) && ((chMult+elMult+muMult) > 0) && (eef < 0.99)))
            return false;
        return (nhef < 0.9) && (pef < 0.9) && ((chMult+nhMult+phMult+elMult+muMult) > 1);
    } else {
        return (pef < 0.9 && (nhMult + phMult) > 10);
    }
}


bool tightLepVetoCleaning(float eta,
                          float chef, float nhef, float pef, float eef, float mef, float hfhef, float hfemef,
                          short chMult, short nhMult, short phMult, short elMult, short muMult, short hfhMult, short hfemMult) {
    if (fabs(eta) <= 3) {
        if ((fabs(eta) <= 2.4) && !((chef > 0) && ((chMult+elMult+muMult) > 0) && (eef < 0.9)))
            return false;
        return (nhef < 0.9) && (pef < 0.9) && ((chMult+nhMult+phMult+elMult+muMult) > 1) && (mef < 0.8) && (muMult == 0) && (elMult == 0);
    } else {
        return (pef < 0.9 && (nhMult + phMult) > 10);
    }
}


template<typename T>
int findRecoJetIndex(T et, T eta, T phi, const L1AnalysisRecoJetDataFormat & jets) {
    for (unsigned i = 0; i < jets.nJets; ++i){
        // match two floating-point numbers: use range of acceptibility rather than ==
      if (//fabs(jets.etCorr[i] - et) < 0.01 // keeping that condition caused errors when running matching between PF and Gen
	    /* &&*/ fabs(jets.eta[i] - eta) < 0.01
            && fabs(jets.phi[i] - phi) < 0.01)
            return i;
    }
    return -1;
}
template int findRecoJetIndex(float et, float eta, float phi, const L1AnalysisRecoJetDataFormat & jets);
template int findRecoJetIndex(double et, double eta, double phi, const L1AnalysisRecoJetDataFormat & jets);


bool checkTriggerFired(const std::vector<TString> & hlt, const std::string & selection) {
    for (const auto & hltItr: hlt) {
        if (std::string(hltItr).find(selection) != std::string::npos)
            return true;
    }
    return false;
}


float scalarSumPt(std::vector<TLorentzVector> jets) {
    float sum = 0.;
    for (const auto& itr: jets) {
        sum += itr.Pt();
    }
    return sum;
}


TLorentzVector vectorSum(std::vector<TLorentzVector> jets) {
    TLorentzVector sum;
    for (const auto& itr: jets) {
        sum += itr;
    }
    return sum;
}


std::vector<TLorentzVector> getJetsForHTT(std::vector<TLorentzVector> jets) {
    std::vector<TLorentzVector> outputJets;
    for (const auto& itr: jets) {
        if (passHTTCut(itr))
            outputJets.push_back(itr);
    }
    return outputJets;
}


bool passHTTCut(TLorentzVector jet) {
    return (jet.Pt() > 30 && fabs(jet.Eta()) <= 3);
}
