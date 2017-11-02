#include "TFile.h"
#include "TF1.h"
#include <iostream>
#include <fstream>

// HOW TO RUN
// $ root -q -b -l $CMSSW_BASE/src/L1Trigger/L1JetEnergyCorrections/bin/local_L1JEC_scripts/writeParamsForLUT.cxx

// only run this code after using tuneFits to massage fits
// (this is incredibly hard coded sorry...)

void writeParamsForLUT()
{

	// SELECT THE INPUT AND OUTPUT FILES
  std::string inputFile = "/storage/eb16003/TEST_Calibs_JEC/test_calibs_with_massaging_v2.root";
  std::string outputFile = "/storage/eb16003/TEST_Calibs_JEC/test_calibs_with_massaging_v2.txt";

	TFile * f = TFile::Open(inputFile.c_str());
	TF1 * g00 = (TF1*)f->Get("EDITFIT_fitfcneta_0_0.435");
	TF1 * g01 = (TF1*)f->Get("EDITFIT_fitfcneta_0.435_0.783");
	TF1 * g02 = (TF1*)f->Get("EDITFIT_fitfcneta_0.783_1.131");
	TF1 * g03 = (TF1*)f->Get("EDITFIT_fitfcneta_1.131_1.305");
	TF1 * g04 = (TF1*)f->Get("EDITFIT_fitfcneta_1.305_1.479");
	TF1 * g05 = (TF1*)f->Get("EDITFIT_fitfcneta_1.479_1.653");
	TF1 * g06 = (TF1*)f->Get("EDITFIT_fitfcneta_1.653_1.83");
	TF1 * g07 = (TF1*)f->Get("EDITFIT_fitfcneta_1.83_1.93");
	TF1 * g08 = (TF1*)f->Get("EDITFIT_fitfcneta_1.93_2.043");
	TF1 * g09 = (TF1*)f->Get("EDITFIT_fitfcneta_2.043_2.172");
	TF1 * g10 = (TF1*)f->Get("EDITFIT_fitfcneta_2.172_2.322");
	TF1 * g11 = (TF1*)f->Get("EDITFIT_fitfcneta_2.322_2.5");
	TF1 * g12 = (TF1*)f->Get("EDITFIT_fitfcneta_2.5_2.964");
	TF1 * g13 = (TF1*)f->Get("EDITFIT_fitfcneta_2.964_3.489");
	TF1 * g14 = (TF1*)f->Get("EDITFIT_fitfcneta_3.489_4.191");
	TF1 * g15 = (TF1*)f->Get("EDITFIT_fitfcneta_4.191_5.191");

	ofstream myfile;
	myfile.open(outputFile.c_str());

	myfile << g00->GetParameter(0) << ", ";
	myfile << g00->GetParameter(1) << ", ";
	myfile << g00->GetParameter(2) << ", ";
	myfile << g00->GetParameter(3) << ", ";
	myfile << g00->GetParameter(4) << ", ";
	myfile << g00->GetParameter(5) << ", ";
	myfile << g00->GetParameter(6) << ", ";
	myfile << g00->Eval(g00->GetXmin()) << ", ";
	myfile << g00->GetXmin() << ", ";
	myfile << g00->Eval(g00->GetXmax()) << ", ";
	myfile << g00->GetXmax() << std::endl;

	myfile << g01->GetParameter(0) << ", ";
	myfile << g01->GetParameter(1) << ", ";
	myfile << g01->GetParameter(2) << ", ";
	myfile << g01->GetParameter(3) << ", ";
	myfile << g01->GetParameter(4) << ", ";
	myfile << g01->GetParameter(5) << ", ";
	myfile << g01->GetParameter(6) << ", ";
	myfile << g01->Eval(g01->GetXmin()) << ", ";
	myfile << g01->GetXmin() << ", ";
	myfile << g01->Eval(g01->GetXmax()) << ", ";
	myfile << g01->GetXmax() << std::endl;

	myfile << g02->GetParameter(0) << ", ";
	myfile << g02->GetParameter(1) << ", ";
	myfile << g02->GetParameter(2) << ", ";
	myfile << g02->GetParameter(3) << ", ";
	myfile << g02->GetParameter(4) << ", ";
	myfile << g02->GetParameter(5) << ", ";
	myfile << g02->GetParameter(6) << ", ";
	myfile << g02->Eval(g02->GetXmin()) << ", ";
	myfile << g02->GetXmin() << ", ";
	myfile << g02->Eval(g02->GetXmax()) << ", ";
	myfile << g02->GetXmax() << std::endl;

	myfile << g03->GetParameter(0) << ", ";
	myfile << g03->GetParameter(1) << ", ";
	myfile << g03->GetParameter(2) << ", ";
	myfile << g03->GetParameter(3) << ", ";
	myfile << g03->GetParameter(4) << ", ";
	myfile << g03->GetParameter(5) << ", ";
	myfile << g03->GetParameter(6) << ", ";
	myfile << g03->Eval(g03->GetXmin()) << ", ";
	myfile << g03->GetXmin() << ", ";
	myfile << g03->Eval(g03->GetXmax()) << ", ";
	myfile << g03->GetXmax() << std::endl;

	myfile << g04->GetParameter(0) << ", ";
	myfile << g04->GetParameter(1) << ", ";
	myfile << g04->GetParameter(2) << ", ";
	myfile << g04->GetParameter(3) << ", ";
	myfile << g04->GetParameter(4) << ", ";
	myfile << g04->GetParameter(5) << ", ";
	myfile << g04->GetParameter(6) << ", ";
	myfile << g04->Eval(g04->GetXmin()) << ", ";
	myfile << g04->GetXmin() << ", ";
	myfile << g04->Eval(g04->GetXmax()) << ", ";
	myfile << g04->GetXmax() << std::endl;

	myfile << g05->GetParameter(0) << ", ";
	myfile << g05->GetParameter(1) << ", ";
	myfile << g05->GetParameter(2) << ", ";
	myfile << g05->GetParameter(3) << ", ";
	myfile << g05->GetParameter(4) << ", ";
	myfile << g05->GetParameter(5) << ", ";
	myfile << g05->GetParameter(6) << ", ";
	myfile << g05->Eval(g05->GetXmin()) << ", ";
	myfile << g05->GetXmin() << ", ";
	myfile << g05->Eval(g05->GetXmax()) << ", ";
	myfile << g05->GetXmax() << std::endl;

	myfile << g06->GetParameter(0) << ", ";
	myfile << g06->GetParameter(1) << ", ";
	myfile << g06->GetParameter(2) << ", ";
	myfile << g06->GetParameter(3) << ", ";
	myfile << g06->GetParameter(4) << ", ";
	myfile << g06->GetParameter(5) << ", ";
	myfile << g06->GetParameter(6) << ", ";
	myfile << g06->Eval(g06->GetXmin()) << ", ";
	myfile << g06->GetXmin() << ", ";
	myfile << g06->Eval(g06->GetXmax()) << ", ";
	myfile << g06->GetXmax() << std::endl;

	myfile << g07->GetParameter(0) << ", ";
	myfile << g07->GetParameter(1) << ", ";
	myfile << g07->GetParameter(2) << ", ";
	myfile << g07->GetParameter(3) << ", ";
	myfile << g07->GetParameter(4) << ", ";
	myfile << g07->GetParameter(5) << ", ";
	myfile << g07->GetParameter(6) << ", ";
	myfile << g07->Eval(g07->GetXmin()) << ", ";
	myfile << g07->GetXmin() << ", ";
	myfile << g07->Eval(g07->GetXmax()) << ", ";
	myfile << g07->GetXmax() << std::endl;

	myfile << g08->GetParameter(0) << ", ";
	myfile << g08->GetParameter(1) << ", ";
	myfile << g08->GetParameter(2) << ", ";
	myfile << g08->GetParameter(3) << ", ";
	myfile << g08->GetParameter(4) << ", ";
	myfile << g08->GetParameter(5) << ", ";
	myfile << g08->GetParameter(6) << ", ";
	myfile << g08->Eval(g08->GetXmin()) << ", ";
	myfile << g08->GetXmin() << ", ";
	myfile << g08->Eval(g08->GetXmax()) << ", ";
	myfile << g08->GetXmax() << std::endl;

	myfile << g09->GetParameter(0) << ", ";
	myfile << g09->GetParameter(1) << ", ";
	myfile << g09->GetParameter(2) << ", ";
	myfile << g09->GetParameter(3) << ", ";
	myfile << g09->GetParameter(4) << ", ";
	myfile << g09->GetParameter(5) << ", ";
	myfile << g09->GetParameter(6) << ", ";
	myfile << g09->Eval(g09->GetXmin()) << ", ";
	myfile << g09->GetXmin() << ", ";
	myfile << g09->Eval(g09->GetXmax()) << ", ";
	myfile << g09->GetXmax() << std::endl;

	myfile << g10->GetParameter(0) << ", ";
	myfile << g10->GetParameter(1) << ", ";
	myfile << g10->GetParameter(2) << ", ";
	myfile << g10->GetParameter(3) << ", ";
	myfile << g10->GetParameter(4) << ", ";
	myfile << g10->GetParameter(5) << ", ";
	myfile << g10->GetParameter(6) << ", ";
	myfile << g10->Eval(g10->GetXmin()) << ", ";
	myfile << g10->GetXmin() << ", ";
	myfile << g10->Eval(g10->GetXmax()) << ", ";
	myfile << g10->GetXmax() << std::endl;

	myfile << g11->GetParameter(0) << ", ";
	myfile << g11->GetParameter(1) << ", ";
	myfile << g11->GetParameter(2) << ", ";
	myfile << g11->GetParameter(3) << ", ";
	myfile << g11->GetParameter(4) << ", ";
	myfile << g11->GetParameter(5) << ", ";
	myfile << g11->GetParameter(6) << ", ";
	myfile << g11->Eval(g11->GetXmin()) << ", ";
	myfile << g11->GetXmin() << ", ";
	myfile << g11->Eval(g11->GetXmax()) << ", ";
	myfile << g11->GetXmax() << std::endl;

	myfile << g12->GetParameter(0) << ", ";
	myfile << g12->GetParameter(1) << ", ";
	myfile << g12->GetParameter(2) << ", ";
	myfile << g12->GetParameter(3) << ", ";
	myfile << g12->GetParameter(4) << ", ";
	myfile << g12->GetParameter(5) << ", ";
	myfile << g12->GetParameter(6) << ", ";
	myfile << g12->Eval(g12->GetXmin()) << ", ";
	myfile << g12->GetXmin() << ", ";
	myfile << g12->Eval(g12->GetXmax()) << ", ";
	myfile << g12->GetXmax() << std::endl;

	myfile << g13->GetParameter(0) << ", ";
	myfile << g13->GetParameter(1) << ", ";
	myfile << g13->GetParameter(2) << ", ";
	myfile << g13->GetParameter(3) << ", ";
	myfile << g13->GetParameter(4) << ", ";
	myfile << g13->GetParameter(5) << ", ";
	myfile << g13->GetParameter(6) << ", ";
	myfile << g13->Eval(g13->GetXmin()) << ", ";
	myfile << g13->GetXmin() << ", ";
	myfile << g13->Eval(g13->GetXmax()) << ", ";
	myfile << g13->GetXmax() << std::endl;

	myfile << g14->GetParameter(0) << ", ";
	myfile << g14->GetParameter(1) << ", ";
	myfile << g14->GetParameter(2) << ", ";
	myfile << g14->GetParameter(3) << ", ";
	myfile << g14->GetParameter(4) << ", ";
	myfile << g14->GetParameter(5) << ", ";
	myfile << g14->GetParameter(6) << ", ";
	myfile << g14->Eval(g14->GetXmin()) << ", ";
	myfile << g14->GetXmin() << ", ";
	myfile << g14->Eval(g14->GetXmax()) << ", ";
	myfile << g14->GetXmax() << std::endl;					

	myfile << g15->GetParameter(0) << ", ";
	myfile << g15->GetParameter(1) << ", ";
	myfile << g15->GetParameter(2) << ", ";
	myfile << g15->GetParameter(3) << ", ";
	myfile << g15->GetParameter(4) << ", ";
	myfile << g15->GetParameter(5) << ", ";
	myfile << g15->GetParameter(6) << ", ";
	myfile << g15->Eval(g15->GetXmin()) << ", ";
	myfile << g15->GetXmin() << ", ";
	myfile << g15->Eval(g15->GetXmax()) << ", ";
	myfile << g15->GetXmax() << std::endl;	

	myfile.close();
}
