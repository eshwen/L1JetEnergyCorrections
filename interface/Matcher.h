#ifndef L1Trigger_L1JetEnergyCorrections_Matcher_h
#define L1Trigger_L1JetEnergyCorrections_Matcher_h
// -*- C++ -*-
//
// Package:     L1Trigger/L1JetEnergyCorrections
// Class  :     Matcher
//
/**\class Matcher Matcher.h "L1Trigger/L1JetEnergyCorrections/interface/Matcher.h"

 Description: Base class that defines interface for all Matcher implementations.

 Usage:
    <usage>

*/
//
// Original Author:  Robin Cameron Aggleton
//         Created:  Wed, 12 Nov 2014 21:17:23 GMT
//
#include <iostream>

#include "TLorentzVector.h"
#include "TGraph.h"
#include "TMultiGraph.h"

#include "MatchedPair.h"
/**
 * @brief Base class that defines interface for all Matcher implementations.
 * @details A "Matcher" takes in 2 collections: one reference jet collection, and
 * one collection of L1 jets. It outputs pairs of reference & L1 jets that
 * "match" based on some criteria. Different matching schemes should be
 * implemented as classes that inherit from this class. This keeps a
 * consistent, clean interface for whatever program is using a Matcher derivation.
 */
class Matcher
{

public:

    /**
     * @brief Set reference jet collection (e.g. GenJets)
     *
     * @param refJets std::vector of TLorentzVector holding reference jets
     */
    virtual void setRefJets(const std::vector<TLorentzVector>& refJets) = 0;

    /**
     * @brief Set L1 jet collection (e.g. from GCT)
     *
     * @param l1Jets std::vector of TLorentzVector holding L1 jets
     */
    virtual void setL1Jets(const std::vector<TLorentzVector>& l1Jets) = 0;

    /**
     * @brief Produce pairs of L1 jets matched to reference jets based on some criteria.
     * @details Details of how matching is done will be provided by derived classes.
     * @return Returns a vector of MatchedPair objects, each hold matching ref & L1 jet.
     */
    virtual std::vector<MatchedPair> getMatchingPairs() = 0;

    /**
     * @brief Access ref jet collection used in matching process
     */
    virtual std::vector<TLorentzVector> getRefJets() const { return refJets_; };

    /**
     * @brief Access L1 jet collection used in matching process
     */
    virtual std::vector<TLorentzVector> getL1Jets() const { return l1Jets_; };

    /**
     * @brief Overload ostream operator.
     * @details Can do different message for derived classes
     * by overloading the printName() method
     */
    friend std::ostream& operator<< (std::ostream& os, const Matcher& mat) {
        return mat.printName(os);
    };

    /**
     * @brief Debug function to print out details of matching pairs.
     */
    virtual void printMatches() const {
        std::cout << "Matches:" << std::endl;
        if (matchedJets_.size() != 0) {
            for (auto &it: matchedJets_) { std::cout << it << std::endl; }
        } else { std::cout << "<NONE>" << std::endl; };
    };


protected:
    std::vector<TLorentzVector> refJets_; //!< to store reference jet collection
    std::vector<TLorentzVector> l1Jets_; //!< to store L1 jet collection
    std::vector<MatchedPair> matchedJets_; //!< to store matches

private:
    /**
     * @brief Dunction to print out basic details, used by ostream operator.
     */
    virtual std::ostream& printName(std::ostream& os) const {
        return os << "I am a abstract Matcher. Please overload printName().\n";
    };
};

#endif /* L1JetEnergyCorrections_Matcher_h */
