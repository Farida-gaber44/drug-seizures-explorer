"""Build data/reference/drug_class_lookup.csv: one row per drug name found in the IDS data.

Columns:
  drug            name exactly as in the data
  unodc_class     UNODC drug class (from the official 'Drug list' sheet, or assigned by hand)
  project_group   the "plants to labs" grouping used in this project:
                  Plant-based | Synthetic | Pharmaceutical | New psychoactive substances |
                  Precursors & chemicals | Other / unspecified
  mapping_source  'unodc_list' or 'manual' (manual = name not in UNODC's list, classified by hand)

Plant-based means made from a plant (cannabis, coca/cocaine, opium/heroin, khat, kratom),
even if processed in a lab. The CSV can be edited by hand; 04_clean.py reads it as is.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PLANT, SYN, PHARMA, NPS = "Plant-based", "Synthetic", "Pharmaceutical", "New psychoactive substances"
CHEM, OTHER = "Precursors & chemicals", "Other / unspecified"

CLASS_TO_GROUP = {
    "Cannabis-type (excluding synthetic cannabinoids)": PLANT,
    "Cocaine-type": PLANT,
    "Amphetamine-type stimulants (excluding ecstasy)": SYN,
    "“Ecstasy”-type substances": SYN,
    "Hallucinogens": SYN,
    "New psychoactive substances": NPS,
    "Sedatives and Tranquillizers": PHARMA,
    "Precursors": CHEM,
    "Other chemicals": CHEM,
    "Non-specified psychotropic substances": OTHER,
    "Other drugs/substances": OTHER,
    "Solvents and Inhalants": OTHER,
}
OPIOID_SUBGROUP_TO_GROUP = {"Opiates": PLANT, "Pharmaceutical opioids": PHARMA, "Other opioids": SYN}

# Names in UNODC's list whose class-level group does not fit
OVERRIDES = {
    "Opium": PLANT, "Poppy plants": PLANT, "Poppy seeds": PLANT, "Poppy straw": PLANT,
    "Non-specified opiates": PLANT, "Other opiates": PLANT,
    "Non-specified opioids": OTHER, "Other opioids": OTHER,
    "Fentanyl": SYN, "Psilocybin": PLANT, "Khat": PLANT, "Mitragyna speciosa (kratom)": PLANT,
    "Tetrahydrocannabinol (THC)": PLANT, "Tetrahydrocannabinolic Acid (THCA)": PLANT,
    "Pregabalin": PHARMA, "Non-specified synthetic drugs/substances": SYN,
    "Dimethyl ether": CHEM, "Calcium carbonate": CHEM, "Calcium Oxide": CHEM,
    "Ethyl acetate": CHEM, "Non-specified adulterants": CHEM,
}

ATS, ECS, HAL = "Amphetamine-type stimulants (excluding ecstasy)", "“Ecstasy”-type substances", "Hallucinogens"
OPI, SED = "Opioids", "Sedatives and Tranquillizers"
NPSC, PRE, OTH = "New psychoactive substances", "Precursors", "Other drugs/substances"
CANN, COC = "Cannabis-type (excluding synthetic cannabinoids)", "Cocaine-type"

# Names not in UNODC's list: (unodc_class, project_group)
MANUAL = {
    # plant-based
    "Cannabis Leaves": (CANN, PLANT), "Edible cannabis": (CANN, PLANT), "Liquid cocaine": (COC, PLANT),
    "Extract from Opium poppy": (OPI, PLANT), "Pavots": (OPI, PLANT),
    "6-Monoacetylmorphine": (OPI, PLANT), "6-Monoacetylcodeine": (OPI, PLANT),
    "Salvinorin": (NPSC, PLANT), "Lactuca virosa": (NPSC, PLANT), "Leonotis leonurus": (NPSC, PLANT),
    "Turnera diffusa": (NPSC, PLANT), "Mitragynine": (NPSC, PLANT),
    # synthetic (classic lab drugs)
    "Liquid methamphetamine": (ATS, SYN), "Dimethylamphetamine": (ATS, SYN), "Pipradrol": (ATS, SYN),
    "Yava": (ATS, SYN), "para-Methoxyamphetamine": (ECS, SYN), "para-Methoxy-N-methylamphetamine": (ECS, SYN),
    "MMDA": (ECS, SYN), "MBDB": (ECS, SYN), "MDMA & Mephedrone": (ECS, SYN),
    "Amphetamine-Ketamine Mix": (ATS, SYN), "DOB": (HAL, SYN), 'STP ("DOM")': (HAL, SYN),
    "GHB/GBL": (SED, SYN), "MPPP": (OPI, SYN), "Alpha-Methylfentanyl": (OPI, SYN), "Phentanyl": (OPI, SYN),
    "6-Desoxycodeine": (OPI, SYN), "Synthetics": (OTH, SYN),
    # pharmaceutical
    "Non-specified pharmaceuticals": (OTH, PHARMA), "GABA": (OTH, PHARMA), "Taren": (OTH, PHARMA),
    "Parkedil": (OTH, PHARMA), "Parkenal": (OTH, PHARMA), "Cough sirups": (OPI, PHARMA),
    "Phensydyl": (OPI, PHARMA), "Flunitrazepam (Disomnilan, Flumipam, Rophynol)": (SED, PHARMA),
    "Dextromethorphan": (OTH, PHARMA), "Substitol (slow release Morphine)": (OPI, PHARMA),
    "Orzepam": (SED, PHARMA), "Lysanxia": (SED, PHARMA), "TRANKXENEK": (SED, PHARMA),
    "Clorazepate": (SED, PHARMA), "Nozepane": (SED, PHARMA), "Novazine": (SED, PHARMA),
    "Lozenal": (SED, PHARMA), "Zopalet": (SED, PHARMA), "Roche": (SED, PHARMA), "Zirexa": (SED, PHARMA),
    "Trihexiphenidyl": (OTH, PHARMA), "Sinequan (Doxepine)": (OTH, PHARMA), "Largactile": (OTH, PHARMA),
    "Equinil (Meprobamates)": (SED, PHARMA), "Dextropoxyphene": (OPI, PHARMA),
    "Dextropropoxyphene": (OPI, PHARMA), "Codidol": (OPI, PHARMA), "Halbiridol": (OTH, PHARMA),
    "Spasmo proxyvon": (OPI, PHARMA), "ANAFRANIL (CLOMIPRAMINE)": (OTH, PHARMA), "Somnubene": (SED, PHARMA),
    "BUSPAR (CHYDRATE DE BUSPIRONE)": (SED, PHARMA), "Amobarbital": (SED, PHARMA), "Tilidate": (OPI, PHARMA),
    "Butorphanol": (OPI, PHARMA), "Tapentadol": (OPI, PHARMA), "Ludiomil (Maprotiline)": (OTH, PHARMA),
    "Ethyl loflazepate": (SED, PHARMA), "Elavil (Amitriptyline)": (OTH, PHARMA), "LIOREZAL": (OTH, PHARMA),
    "Diphenoxylate": (OPI, PHARMA), "Tofranil (Imipramine)": (OTH, PHARMA), "Karcidone": (OTH, PHARMA),
    "Carbamazepine": (OTH, PHARMA), "Tofisopam": (SED, PHARMA), "Seresta (Oxazepam)": (SED, PHARMA),
    "Soulperane": (OTH, PHARMA), "Anabolic steroids": (OTH, PHARMA), "Amantadine": (OTH, PHARMA),
    "Levomethorphan": (OPI, PHARMA), "Amfepramone Hydrochloride": (ATS, PHARMA),
    "Phendimetrazine": (ATS, PHARMA), "Benzphetamine": (ATS, PHARMA), "Fenfluramine": (ATS, PHARMA),
    "Modafinil": (ATS, PHARMA), "Retalin Tablets": (ATS, PHARMA),
    # precursors & chemicals
    "Quinoline": (PRE, CHEM), "Methylester": (PRE, CHEM), "Methyl ether": (PRE, CHEM), "Iodine": (PRE, CHEM),
    "Acetone/Ethyl Ether": (PRE, CHEM), "Phosphorous Acid": (PRE, CHEM), "Phenylacetone": (PRE, CHEM),
    "Sodium hydroxide": (PRE, CHEM), "Pyrrolidine": (PRE, CHEM), "Hypophosphorous Acid": (PRE, CHEM),
    "Methylsulfonylmethane": (PRE, CHEM), "Cyclohexanone": (PRE, CHEM), "Methyl Ethyl Ketone": (PRE, CHEM),
    "Dimethylamine": (PRE, CHEM), "PMK-glycidate": (PRE, CHEM), "APAA": (PRE, CHEM),
    "Phenyl-2-nitropropene": (PRE, CHEM), "Ammonia Sprit": (PRE, CHEM),
    # other / unknown
    "Other drugs/substances": (OTH, OTHER), "Non-specified stimulants": (OTH, OTHER),
    "Controlled Drug Mix": (OTH, OTHER), "Kitil": (OTH, OTHER), "Colina": (OTH, OTHER),
    "Fuelite": (OTH, OTHER),
}
# Every other unlisted name is a new psychoactive substance (synthetic cannabinoids,
# cathinones, tryptamines, phenethylamines, piperazines, PCP-type); checked by hand.


def main() -> None:
    out_dir = ROOT / "data" / "reference"
    out_dir.mkdir(parents=True, exist_ok=True)
    names = pd.read_parquet(ROOT / "data" / "interim" / "ids_raw.parquet", columns=["drug"])["drug"]
    names = names.value_counts().rename_axis("drug").reset_index(name="rows")
    unodc = pd.read_csv(ROOT / "data" / "interim" / "unodc_drug_list.csv").drop_duplicates("drug")
    lookup = names.merge(unodc, on="drug", how="left")

    def classify(r):
        if pd.notna(r.drug_class):
            if r.drug in OVERRIDES:
                group = OVERRIDES[r.drug]
            elif r.drug_class == OPI:
                group = OPIOID_SUBGROUP_TO_GROUP.get(r.drug_subgroup, OTHER)
            else:
                group = CLASS_TO_GROUP[r.drug_class]
            return r.drug_class, group, "unodc_list"
        if r.drug in MANUAL:
            return (*MANUAL[r.drug], "manual")
        return NPSC, NPS, "manual"

    lookup[["unodc_class", "project_group", "mapping_source"]] = lookup.apply(classify, axis=1, result_type="expand")
    lookup = lookup[["drug", "unodc_class", "project_group", "mapping_source", "rows"]]
    lookup.to_csv(out_dir / "drug_class_lookup.csv", index=False, encoding="utf-8")

    print(f"{len(lookup)} drug names classified ({(lookup.mapping_source == 'manual').sum()} by hand)")
    print(lookup.groupby("project_group")["rows"].agg(["count", "sum"]).rename(
        columns={"count": "drug_names", "sum": "rows"}).to_string())


if __name__ == "__main__":
    main()
