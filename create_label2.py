from patient.models import Label, AlternateLabel
import json
import datetime


def main():
    input_data = [
        "Haemoglobin", "RBC Count", "MCV", "MCH", "TLC", "PCV", "MCHC", "MPV", "E.S.R.", "GLUCOSE", "SGOT- ASPARTTATE TRANSAMINAS E", "SGPT - ALANINE TRANSAMINAS E", "GGTP", "UIBC", "FOLATE", "GLYCOSYLATE D HEMOGLOBIN", "25-HYDROXY, VITAMIN D" ,
        "HAEMOGLOBIN", "TOTAL LEUCOCYTES COUNT","PACKED CELLS UME", "MEAN CORP VOLUME", "MEAN CORP Hb ( MCH)", "MEAN CORP Hb CONC", "PLATELETS COUNT", "E.S.R.", "Neutrophil", "Lymphocyte", "Monocyte", "Eosinophil", "Basophil", "Serum Cholestrol", "Serum Triglycerides", "HDL Cholesterol", "Serum L.D.L.Cholestrol", "Serum VLDL", "CHO / HDL Cholesterol Ratio", "LDL / HDL Cholesterol Ratio", "BLOOD UREA", "BLOOD UREA NITROGEN", "Serum Creatinine", "Serum Uric Acid ", "Calcium", "Serum Sodium", "Serum Potassium", "Serum Bilirubin", "Bilirubin (Direct)", "Bilirubin (Indirect )", "Serum G. O. T./AST", "Serum G. P. T. /ALT","Serum Alkaline Phosphatase", "GAMMA G.T.", "Serum Albumin", "Globulin", "TRI-IODO THYROXINE", "SERUM TSH", "ESTRADIOL", "(Glycated HbA1c)/ HbA1c", "VITAMIN B-12 LEVEL ", "VITAMIN D3 LEVEL", "LH", "FSH", "Total Protein", "Blood Sugar",
        "HEMOGLOBIN ", "WHITE BLOOD CELL COUNT", "RED BLOOD CELL COUNT", "HEMATOCRIT", "MCV", "MCH", "MCHC", "MPV", "PLATELET COUNT", "ERYTHROCYTE SEDIMENTATION RATE", "NEUTROPHILS ", "LYMPHOCYTES ", "MONOCYTES", "EOSINOPHILS ", "BASOPHILS ", "ABSOLUTE NEUTROPHILS", "ABSOLUTE LYMPHOCYTES", "ABSOLUTE MONOCYTES", "ABSOLUTE BASOPHILS ", "TSH",
        "HEMOGLOBIN","TLC","PACKED CELL VOLUME","MCV","MCH, Blood","MCHC","PLATELET COUNT","E.S.R","POLYMORPHS","LYMPHOCYTES", "EOSINOPHILS" ,"MONOCYTES","RDW","ABSOLUTE NEUTROPHIL COUNT" , "ABSOLUTE EOSINOPHIL COUNT BLOOD","FASTING GLUCOSE","MAGNESIUM","CHOLESTROL, SERUM","TRIGLYCERIDES","HDL CHOLESTEROL","LDL CHOLESTEROL ","VLDL CHOLESTEROL","LDL / HDL RATIO","CHOLESTEROL / HDL RATIO","UREA Serum",  "UREA NITROGEN","CREATININE SERUM","URIC ACID","SODIUM","POTASSIUM","CHLORIDE" ,"BILIRUBIN (TOTAL)","SGOT","SGPT","ALKALINE PHOSPHATASE","TOTAL PROTEINS Serum","ALBUMIN","GLOBULIN","A:G RATIO","IgE SERUM","IRON","TIBC","UIBC","FERRITIN","FT3 Serum" ,"FREE T4","TSH, Serum"," HbA1c","VITAMIN B12","VITAMIN D, 25-HYDROXY, Serum","FOLATE, Serum","INSULIN FASTING","INSULIN PP","BLOOD GLUCOSE PP",
        "Hemoglobin","WBC COUNT","RBC","Packed cell volume","Platelet Count","ESR","Neutrophils","Lymphocytes","Monocytes","Eosinophils","Basophils","CHOLESTEROL", "TRIGLYCERIDES", "HDL CHOLESTEROL", "LDL CHOLESTEROL","HDL CHOLESTROL RATIO","BILIRUBIN","BILIRUBIN CONJUGATED(DIRECT)","BILIRUBIN UNCONJUGATED (INDIRECT)","AST ","ALT","ALKALINE PHOSPHATASE","GGTP","ALBUMIN","GLOBULIN","FREE T3","FREE T4","TSH","HBA1C","VITAMIN B12","VITAMIN D TOTAL(250H vitD3 and 250H vitD2)","FASTING","INSULIN (PP)",
    ]
    input_data = list(map(str.strip, input_data))
    input_data = list(set(map(str.lower, input_data)))
    print(input_data)
    print(len(input_data))
    for label in input_data:
        print(label)
        try:    
            l, created = Label.objects.get_or_create(name=label)
            print(l, created)
            if created:
                l.save()
            a = AlternateLabel.objects.create(name=label, label=l)
            a.save()
        except Exception as identifier:
            print('error', label, identifier,)
    return 'done'


def label():
    with open('labels.json', 'r') as readfile:
        data = json.load(readfile)
    # print(data[0])
    for item, val in data.items():
        val1 = val[0]
        val2 = val[1]
        try:    
            print('here', item, val)
            l, created = Label.objects.get_or_create(name=item, lower_range=val1, upper_range=val2)
        except Exception as identifier:
            print('error', 'aman', label, identifier, )

def alterlabel():
    with open('alternate.json', 'r') as readfile:
        data = json.load(readfile)
    # print(data[0])
    for item, val in data.items():
        try:    
            print('here', item, val)
            l = Label.objects.get(name=val)
            print('got label', label)
            l, created = AlternateLabel.objects.get_or_create(name=item, label=l)
            print('created alternate label', l, created)
        except Exception as identifier:
            print('error', 'aman', label, identifier, )

def blabel():
    labels = Label.objects.all()
    time = str(datetime.datetime.today())
    a = {}
    with open(f'backup_label_{time}.json', 'w') as wf:
        for label in labels:
            a[label.name] = [label.lower_range, label.upper_range]
        json.dump(a, wf)

def balterlabel():
    labels = AlternateLabel.objects.all()
    time = str(datetime.datetime.today())
    a = {}
    with open(f'backup_alternate_label_{time}.json', 'w') as wf:
        for label in labels:
            a[label.name] = label.label.name
        json.dump(a, wf)


if __name__=='__main__':
    pass