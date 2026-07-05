import os
import re  # Regular Expressions for string handling
from contextlib import asynccontextmanager
from functools import lru_cache

import pandas as pd
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    test_sequence = "Ac A E C K(FAM) A E C CONH2"
    sim_ions = { 1: 1153, 2: 577, 3: 385, 4: 289, 5: 231, 6: 193, 7: 166, 8: 145, 9: 129, 10: 116, 11: 106 }
    molwt_ions = { 1: 1153.22, 2: 577.11, 3: 385.08, 4: 289.06, 5: 231.45, 6: 193.04, 7: 165.61, 8: 145.03, 9: 129.03, 10: 116.23, 11: 105.75 }
    hrms_ions = { 1: 1152.365, 2: 576.6864, 3: 384.7935, 4: 288.8471, 5: 231.2792, 6: 192.9007, 7: 165.4874, 8: 144.9274, 9: 128.9364, 10: 116.1435, 11: 105.6766 }
    mol_formula = {'C': 51, 'H': 61, 'O': 18, 'N': 9, 'S': 2, 'Cl': 0, 'I': 0, 'P': 0, 'Br': 0}
    features = calc_features(test_sequence)
    if abs(features["MolWt"] - 1152.2096) > 1e-6:
        raise Exception("Implementation Error", "MolWt for test sequence was not calculated correctly")
    if abs(features["Exact"] - 1151.3572) > 1e-6:
        raise Exception("Implementation Error", "Exact mass for test sequence was not calculated correctly")
    if not features["HPLC-SIM Ions"] == sim_ions:
        raise Exception("Implementation Error", "HPLC-SIM ions for test sequence were not calculated correctly")
    if not features["MolWt Ions"] == molwt_ions:
        raise Exception("Implementation Error", "MolWt ions for test sequence were not calculated correctly")
    if not features["HRMS Ions"] == hrms_ions:
        raise Exception("Implementation Error", "HRMS ions for test sequence were not calculated correctly")
    if not features["Mol Formula"] == mol_formula:
        raise Exception("Implementation Error", "Molecular formula for test sequence were not calculated correctly")
    yield

description = """
The PNA-Peptide-Conjucate Feature Calculation API allows you to calculate important features of these molecules!

The source-code of the API is available on [Github](https://github.com/alexandrev/oligo-tools)
A demo instance of the API is available on [Fly.io](https://pepmass.fly.dev/)

"""

app = FastAPI(
    lifespan=lifespan,
    title="PepMass API",
    version="0.1",
    summary="PNA-Peptide-Conjucate Feature Calculation API",
    description=description,
        contact={
        "name": "PartTimeDataScientist",
        "url": "http://data-science-solutions.de/pepmass",
        "email": "pepmass@data-science-solutions.de",
    },
    license_info={
        "name" : "MIT License",
        "identifier": "MIT"}
    )

origins = [
    "*"
]

# Public, read-only API: allow any origin but do NOT allow credentials.
# Combining allow_origins=["*"] with allow_credentials=True effectively reflects
# any Origin while permitting cookies/Authorization, which is unsafe.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["General information"])
async def main():
    root = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(root, 'masscalc.htm')) as fh:
        data = fh.read()
    return Response(content=data, media_type="text/html")

# async def root():
#     """
#     Returns some general information about the PNA-Peptide Mass Calculation API.
#     """
#     return {"info" : "PNA-Peptide Mass Calculation API",
#             "version" : "0.1"}

@app.get("/script.js", tags=["General information"])
async def main():
    root = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(root, 'script.js')) as fh:
        data = fh.read()
    return Response(content=data, media_type="text/javascript")

# async def root():
#     """
#     Returns some general information about the PNA-Peptide Mass Calculation API.
#     """
#     return {"info" : "PNA-Peptide Mass Calculation API",
#             "version" : "0.1"}

@app.get("/health", tags=["General information"])
async def root():
    """
    Just a simple health endpoint - required e.g. for deployment to fly.io.
    """
    return {"status" : "ok"}

@app.get("/building_blocks", tags=["General information"])
async def building_blocks():
    """
    Returns a list of all supported building blocks for performing calculations.

    **Format of this endpoint is currently WIP and will likely change in the future**
    """
    amino_acids = ""
    for monomer in input_monomers().loc[input_monomers()["Type"]=="Amino Acid", "Group"]:
        amino_acids = amino_acids + monomer + ", "
    pnas = ""
    for monomer in input_monomers().loc[input_monomers()["Type"]=="PNA", "Group"]:
        pnas = pnas + monomer + ", "
    fluorophores = ""
    for monomer in input_monomers().loc[input_monomers()["Type"]=="Fluorophore", "Group"]:
        fluorophores = fluorophores + monomer + ", "
    c_terminal_mods = ""
    for monomer in input_monomers().loc[input_monomers()["Type"]=="C-terminal modification", "Group"]:
        c_terminal_mods = c_terminal_mods + monomer + ", "
    protecting_groups = ""
    for monomer in input_monomers().loc[input_monomers()["Type"]=="Protecting Group", "Group"]:
        protecting_groups = protecting_groups + monomer + ", "

    response = {
        "AminoAcids": amino_acids[:-2],
        "PNAmonomers": pnas[:-2],
        "ProtectingGroups": protecting_groups[:-2],
        "Fluorophores": fluorophores[:-2],
        "CTerminalModifications": c_terminal_mods[:-2]
    }

    return(response)

@app.get("/calc/molwt", tags=["Feature calculation"])
async def exact(sequence: str):
    """
    This endpoint returns the molecular weight of the given input sequence.
    """
    return calc_features(sequence)["MolWt"]

@app.get("/calc/exact", tags=["Feature calculation"])
async def exact(sequence: str):
    """
    This endpoint returns the monoisotopic exact mass of the given input sequence.
    """

    return calc_features(sequence)["Exact"]

@app.get("/calc/sim_ions", tags=["Feature calculation"])
async def exact(sequence: str):
    """
    This endpoint returns the excpecd SIM ions frequently used e.g. in HPLC-purifications.
    
    **ATTENTION:** Not all of them are expected to be seen, this calculation simply lists all **possible** values
    """
    return calc_features(sequence)["HPLC-SIM Ions"]

@app.get("/calc/molwt_ions", tags=["Feature calculation"])
async def exact(sequence: str):
    """
    This endpoint returns multiply charged veriations of the given input sequence (calculated from the molecular weight). Depending on the ionization method and the used mass spectrometer you might observe these multiply charged variatons.


    **ATTENTION:** Not all of them are expected to be seen, this calculation simply lists all **possible** values
    """
    return calc_features(sequence)["MolWt Ions"]

@app.get("/calc/hrms_ions", tags=["Feature calculation"])
async def exact(sequence: str):
    """
    This endpoint returns multiply charged veriations of the given input sequence (calculated from the exact mass). Depending on the ionization method and the used mass spectrometer you might observe these multiply charged variatons.


    **ATTENTION:** Not all of them are expected to be seen, this calculation simply lists all **possible** values
    """
    return calc_features(sequence)["HRMS Ions"]

@app.get("/calc/formula", tags=["Feature calculation"])
async def formula(sequence: str):
    """
    This endpoint returns the molecular formula of the given input sequence.
    """
    return calc_features(sequence)["Mol Formula"]

@app.get("/calc/termination_sequences", tags=["Feature calculation"])
async def terminations(sequence: str):
    """
    This endpoint returns the features of all termination sequences of the given input sequence.
    """
    return calc_features(sequence)["Termination Sequences"]

@app.get("/calc/all_features", tags=["Feature calculation"])
async def all_features(sequence: str):
    """
    This endpoint returns all calculated features in a unified json.
    """
    return calc_features(sequence)

@lru_cache(maxsize=1)
def input_monomers() -> pd.DataFrame:
    # Read properties of monomers from Excel generated .csv-file.
    # Cached: the file is static, so it is parsed once instead of on every
    # lookup (previously re-read from disk hundreds of times per request).
    # Path is resolved relative to this file so it works from any working dir.
    root = os.path.dirname(os.path.abspath(__file__))
    return pd.read_csv(os.path.join(root, 'Massen.csv'), sep=";")

def split_sequence(sequence: str) -> list:
    # Split input string at all whitespaces
    seq = re.split("\s+", sequence.strip())
    seq.reverse()
    return(seq)

def calc_multi_ions(mass: float, adduct: str, weight: str, min_wt: int, max_wt: int, digits: int | None = 4) -> dict:
    multi_ions = {}
    adduct_wt = input_monomers().loc[input_monomers()["Group"]==adduct, weight].values[0]
    for i in range(100,0,-1):
        ion = round((mass + (i * adduct_wt))/i, digits)
        if (ion > min_wt and ion < max_wt):
            multi_ions[i] = ion
    return(multi_ions)

def add_building_block(mass: float, formula: dict, building_block: str, weight: str) -> tuple[float, dict]:
    atoms = ['C', 'H', 'O', 'N', 'S', 'Cl', 'I', 'P', 'Br']

    try:
        mass += (input_monomers().loc[input_monomers()["Group"]==building_block, weight].values[0])
        leaving = (input_monomers().loc[input_monomers()["Group"]==building_block, "Leaving"].values[0])
        for atom in atoms:
            formula[atom] += int(input_monomers().loc[input_monomers()["Group"]==building_block, atom].values[0])

        if leaving != "---":
            mass -= (input_monomers().loc[input_monomers()["Group"]==leaving, weight].values[0])
            for atom in atoms:
                formula[atom] -= int(input_monomers().loc[input_monomers()["Group"]==leaving, atom].values[0])
    except IndexError:
        # Unknown building block: fall back to the "UKN" placeholder for BOTH
        # mass and formula. Previously the formula lookup still used the unknown
        # `building_block`, raising a second IndexError and returning HTTP 500.
        mass += (input_monomers().loc[input_monomers()["Group"]=="UKN", weight].values[0])
        leaving = (input_monomers().loc[input_monomers()["Group"]=="UKN", "Leaving"].values[0])
        for atom in atoms:
            formula[atom] += int(input_monomers().loc[input_monomers()["Group"]=="UKN", atom].values[0])

        if leaving != "---":
            mass -= (input_monomers().loc[input_monomers()["Group"]==leaving, weight].values[0])
            for atom in atoms:
                formula[atom] -= int(input_monomers().loc[input_monomers()["Group"]==leaving, atom].values[0])

    return mass, formula

def calc_features(sequence: str) -> dict:
    molwt = 0
    exact = 0
    formula = {'C': 0, 'H': 0, 'O': 0, 'N': 0, 'S': 0, 'Cl': 0, 'I': 0, 'P': 0, 'Br': 0}
    termination_seq = ""
    termination_seq_df = pd.DataFrame()
    dummy = {'C': 0, 'H': 0, 'O': 0, 'N': 0, 'S': 0, 'Cl': 0, 'I': 0, 'P': 0, 'Br': 0}
    monomers = split_sequence(sequence)
    for idx, monomer in enumerate(monomers):
        # If Monomer contains bracketed statement add the mass of the bracketed monomer as well
        if re.search('\(.*\)', monomer):
            m = re.search('(.*)\((.*)\)', monomer)
            modifier = m.group(2)
            monomer = m.group(1)
            molwt, formula = add_building_block(molwt, formula, monomer, "MolWt")
            molwt, formula = add_building_block(molwt, formula, modifier, "MolWt")
            exact, dummy = add_building_block(exact, dummy, monomer, "Exact")
            exact, dummy = add_building_block(exact, dummy, modifier, "Exact")
            termination_seq = monomer + "(" + modifier + ") " + termination_seq
            if (idx>0 and idx < len(monomers)-1):
                molwt_ac, dummy = add_building_block(molwt, dummy, "Ac", "MolWt")
                exact_ac, dummy = add_building_block(exact, dummy, "Ac", "Exact")
                row = {
                    "Index": idx,
                    "Sequence": termination_seq,
                    "MolWt-H": float(round(molwt,2)),
                    "Exact Mass-H": float(round(exact,4)),
                    "MolWt-Ac": float(round(molwt_ac,2)),
                    "Exact Mass-Ac": float(round(exact_ac,4))
                }
                row_df = pd.DataFrame(data=row, index=[0])
                termination_seq_df = pd.concat([termination_seq_df,row_df], ignore_index=True)            
        # Else only add mass of building block
        else:
            molwt, formula = add_building_block(molwt, formula, monomer, "MolWt")
            exact, dummy = add_building_block(exact, dummy, monomer, "Exact")
            termination_seq = monomer + " " + termination_seq
            if (idx>0 and idx < len(monomers)-1):
                molwt_ac, dummy = add_building_block(molwt, dummy, "Ac", "MolWt")
                exact_ac, dummy = add_building_block(exact, dummy, "Ac", "Exact")
                row = {
                    "Index": idx,
                    "Sequence": termination_seq,
                    "MolWt-H": float(round(molwt,2)),
                    "Exact Mass-H": float(round(exact,4)),
                    "MolWt-Ac": float(round(molwt_ac,2)),
                    "Exact Mass-Ac": float(round(exact_ac,4))
                }
                row_df = pd.DataFrame(data=row, index=[0])
                termination_seq_df = pd.concat([termination_seq_df,row_df], ignore_index=True)

    result = {
        "MolWt": round(molwt,4),
        "Exact": round(exact,4),
        "Mol Formula": formula,
        "HPLC-SIM Ions": calc_multi_ions(molwt, "Hplus", "MolWt", 100, 50000, 0),
        "MolWt Ions": calc_multi_ions(molwt, "Hplus", "MolWt", 100, 50000, 2),
        "HRMS Ions": calc_multi_ions(exact, "Hplus", "Exact", 100, 50000, 4),
        "Termination Sequences" : termination_seq_df.to_dict(orient='records')   
    }
        #"Termination Sequences" : termination_seq_df.to_json(orient="records", lines=False).replace('\"', '*')
    return (result)