import sys
import json
import json
import re
import urllib.request
import textract

from .models import AlternateLabel
# GLOBAL VARS | KEEP DEBUG FALSE IN PRODUCTION
DEBUG = True


# local imports
# from .CleanResponse import clean_response
# TODAYS CHANGE LOG
"""
tried new regex to include 4,900
add unit check to CleanResponse.py
REMOVED RATIO FROM UNIT LIST
"""

# Cleaning operations
def remove_invalid_na_unit_response(responses:list):
    """
    takes the list of responses from process.py, and for the respons in which a single tag name 
    had multiple response with correct unit and unit value "NA", it will suppress response with "NA"
    """
    collected_responses = {}
    
    # separating responses bases on their tag name
    for response in responses:
        curr_name      = response['name']

        # if curr_name is already in collected_responses
        if collected_responses.get(curr_name) is not None:
            collected_responses[curr_name].append( response)
        # if name already exist in collected_responses
        else:
            collected_responses[ curr_name ] = [ response ]

    final_response_list = []
    for tagname in collected_responses:
        unit_set = set(response['Unit'] for response in collected_responses[tagname])
        

        # if there are more than one type of unit than keep only those response
        # which doesn't have NA
        if len(unit_set)>1: 
            final_response_list += [response for response in collected_responses[tagname] if response['Unit']!='NA']
        else:
            final_response_list += collected_responses[tagname]

    return final_response_list



def clean_response(response_dict : dict) -> dict:
    """
    cleans the input dict containing response, to return only those results that are valid

    definition of valid:
        len(str(name))>0
        len(str(value))>0
        len(str(ReadIndex))>0
        str(value) in str(ReadIndex)
        # str(unit) in str(ReadIndex)  not enforced

    possible improvements:
        definition can be improved with stricter restrictions, If unit can be empty or not

    """
    result = []
    response = response_dict['Response']['Result']
    for tag in response:
        name  = tag['name']
        value = tag['Value']
        unit =  tag['Unit']
        ReadIndex = tag['ReadIndex']
        TempSent = tag['TempSent']

        # ASSUMPTION
        # keys name, value, Read Index cannot be empty
        if (len(name)<=0 or len(value)<=0 or len(ReadIndex)<=0 ):
            continue # donot add present response to final result

        # ASSUMPTION
        # ReadIndex contains 'value' and 'Unit'
        # If readindex doesn't contain `Vlaue` and `Unit` then
        # ReadIndex is flawed
        if not (
            str(value) in ReadIndex 
            # and str(unit) in ReadIndex
        ):
            continue # donot add present respone to final result
        
        # if unit is anything except 'NA' and its not is ReadIndex
        # ReadIndex is flawed 
        if (not (unit == 'NA')) and (not (unit in ReadIndex)):
            continue

        # if all the checks passes, then present response is correct 
        # add it to the final result
        result.append(tag)

        # removing invalid na unit responses
        result = remove_invalid_na_unit_response(result)

    return result


###################################################################################################################################################
# DATABASE | DO NOT MODIFY THIS LIST | Only add new items
units_list = ['pmol/l', 'pg/mL', 'ng/dL', 'ug/dL', 'U/mL', 'ulU/mL', 'ng/mL', 'ng/L', 'gm/dL', '%',
              '103/mm3', 'mm/hr', 'Secs', 'mg/L', 'mg/dL', 'g/dL', 'U/L', '/cumm', '/Cu mm', '1000/cumm',
              '1st hour', '10^12/L', 'fl', 'Pg', 'gms/dl', 'U/I', 'ng/ml', 'meq/L', 'uIU/ml', 'uU/ml',
              'mU/L', 'pg/ml', 'nmol/L', 'umol/L', 'IU/mL', 'Thousand/uL', '/100 WBC', 'Million/uL',
              'mm/hr', 'mili/cu.mm', '1043/1', 'x103/pl', 'mm/hour', 'mmol/L', 'Cells/ul',
              'Ru/ml', 'AU/ml', 'mgs/dl', 'mill/cu.mm', 'cells/mm3', 'mm 1st Hr', 'x', '10^3/Î¼I', 
              '1000 / micL', 'mm/1hrs', '10~12/L', '10^12/L', 'mIU/mL', 'Gm%', 'mm/Ist hr', 'Millions/cmm', 
              'cc%', 'pgm', 'MEq/L'] +  ['/cmm', '/cu mm', 'IU/L', 'mm/Ist hr.', 'gm/ dl', 'meq /l']  
              
# these are the units which are being read wrong by textract
wrong_interpreted_units = [
  'mmilst hr.',   # mm/lst hr
  'millions/emm', # million/cm
  'Jourmm',       # /cumm
  'ist hour',     # 1st hour
  'tu/mt',        # IU/MI
  'pmol/!',       #pmol/l
  'gmidl',        # gmidl
  '10%?',         # 10^3 / mm^3
  '10\u00b0%/mm?', #10^3 / mm^3
  'mein',          # mm/hr
  'maid',          # mg/dl
  'mg/d',          #mg/dl
  'gaa',           # mg/dl
  'ua', # U/
  'plu/ml', # ulu/ml
  'plu/mi', # ulu/ml
]
units_list += wrong_interpreted_units
wrong_units = {
  'hr. mmilst': 'mm/lst hr', # due to ordering issue 
  'mmilst hr.':'mm/lst hr',
  
  'jourmm': '/cumm',
  'ist hour': '1st hour',
  'tu/mt': 'iu/mi',
  'pmol/!':'pmol/l',
  'gmidl': 'gm/dl',
  '10%?' : '10^3/mm^3',
  '10\u00b0%/mm?' :'10^3/mm^3',
  'mein' : 'mm/hr',
  'maid': 'mg/dl',
  'mg/d':'mg/dl',
  'gaa':'mg/dl',
  'ua':'U/L',
  'plu/ml':'ulu/ml',
  'plu/mi':'ulu/ml',


  'millions/emm':'millions/cmm',
  'dl gm/': 'gm/dl', # dur to ordering issue
  '/l meq' : 'meg /l', # due to ordering issue,
}

# dict of names which are being extracted wrong all the time.
wrong_names = {
  # correct_name : wrong_name
  '(Glycated HbA1c)/ HbA1c' : '(Glycated HbA1c)/ HbAlc' 
}

# DATABASE ENDS
###################################################################################################################################

# PREPROCESSING DATA BASE
# converting to lower case
units_list = [unit.lower() for unit in units_list]
wrong_units = {str(key).lower():str(item).lower() for key, item in wrong_units.items()}
wrong_names = {str(key).lower():str(item).lower() for key,  item in wrong_names.items()}


# changing all units to lower
units_list = [unit.lower() for unit in units_list]
#%%
def download_file(download_url):
    filename = "document.pdf"
    response = urllib.request.urlopen(download_url)
    file = open(filename, 'wb')
    file.write(response.read())
    file.close()
    return filename

# utility function
def invert_dict_mapping(dict_):
  """
  utility function to reverse key, value pair in dictionary
  """
  reversed_mapping_dict = dict(map(reversed, dict_.item()))
  return reversed_mapping_dict

def replace_wrong_read_units(unit : str, wrong_units: dict, sentence: str) -> str:
  """
  check if the unit is one of unit in `wrong_units` and replaces in by correct one
  also change the unit in sentence
  @param:
    unit : str, unit name
    wrong_units : dict, key value pair of wrong unit and right units
    sentence : sentence that contains the unit
  """
  # changing to lower case
  # wrong_units = {k.lower():v.lower for k,v in wrong_units.items()}
  # unit = unit.lower()


  # try to get unit wrong units
  correct_unit = wrong_units.get(unit)
  
  # if unit is not in wrong_units, then return original unit
  if correct_unit is None:
    correct_unit = unit

  # replacing wrong unit with correct in sentence
  try:
    sentence = sentence.replace(unit, correct_unit)
    pass
  except Exception as e:
    if DEBUG:
      print('ERROR WHILE CHANGING SENTENCE')
      print(e)
    pass  
  return correct_unit, sentence

def replace_wrong_read_name(name : str, wrong_names: dict) -> str:
  """
  this function replaces the names which are known for the fact to be wrong with correct names.
  @param:
    name : str, name
    wrong_names : dict, key value pair of wrong name and right name
  """
  # changing to lower case
  # wrong_names = {k.lower():v.lower() for k, v in wrong_names.items()}
  # name = name.lower()

  # try to get unit wrong units
  correct_name = wrong_names.get(name)
  
  # if unit is not in wrong_units, then return original unit
  if correct_name is None:
    correct_name = name
  return correct_name


if DEBUG:
  # input_data = ["process.py", "https://trello-attachments.s3.amazonaws.com/5e9da18088805c67591114a8/5e9da1991a8c9967c7f45e42/88e8799a24eb3588387e806f314e6db7/LIFELINE.pdf",
  #             "Hemoglobin", "NEUTROPHIL", "LYMPHOCYTES", "PLATELET COUNT"]
  input_data = ["process.py", "https://trello-attachments.s3.amazonaws.com/5e9da18088805c67591114a8/5e9da1991a8c9967c7f45e42/0487b155aa77d24458ffe076e71571bc/SANJEEVANI.PDF",
    # "E.S.R."
                          "HAEMOGLOBIN", "TOTAL LEUCOCYTES COUNT ", "RED BLOOD CELL COUNT","PACKED CELLS VOLUME", "MEAN CORP VOLUME", "MEAN CORP Hb ( MCH)", "MEAN CORP Hb CONC ", "PLATELETS COUNT", "E.S.R.", "Neutrophil", "Lymphocyte", "Monocyte", "Eosinophil", "Basophil", "Serum Cholestrol", "Serum Triglycerides", "HDL Cholesterol", "Serum L.D.L.Cholestrol", "Serum VLDL", "CHO / HDL Cholesterol Ratio", "LDL / HDL Cholesterol Ratio", "BLOOD UREA", "BLOOD UREA NITROGEN", "Serum Creatinine", "Serum Uric Acid ", "Calcium", "Serum Sodium", "Serum Potassium", "Serum Bilirubin", "Bilirubin (Direct)", "Bilirubin (Indirect )", "Serum G. O. T./AST", "Serum G. P. T. /ALT","Serum Alkaline Phosphatase", "GAMMA G.T.", "Serum Albumin", "Globulin", "TRI-IODO THYROXINE", "SERUM TSH", "ESTRADIOL", "(Glycated HbA1c)/ HbA1c", "VITAMIN B-12 LEVEL ", "VITAMIN D3 LEVEL", "LH", "FSH", "Total Protein", "Blood Sugar"
    #  '(Glycated HbA1c)/ HbA1c'
    # "Serum Albumin"
     ]
  # input_data = ["process.py", "https://trello-attachments.s3.amazonaws.com/5e9da18088805c67591114a8/5e9da1991a8c9967c7f45e42/2ebc26f2812765b2e3520944493b2cbc/QUEST.pdf",
        # "HEMOGLOBIN ", "WHITE BLOOD CELL COUNT ", "RED BLOOD CELL COUNT ", "HEMATOCRIT ", "MCV", "MCH", "MCHC", "MPV", "PLATELET COUNT ", "ERYTHROCYTE SEDIMENTATION RATE ", "NEUTROPHILS ", "LYMPHOCYTES ", "MONOCYTES", "EOSINOPHILS ", "BASOPHILS ", "ABSOLUTE NEUTROPHILS", "ABSOLUTE LYMPHOCYTES", "ABSOLUTE MONOCYTES", "ABSOLUTE BASOPHILS ", "TSH"
  #             # 'ABSOLUTE NEUTROPHILS'
  #             ]
  # 'pdf_url": "https://trello-attachments.s3.amazonaws.com/5e9da18088805c67591114a8/5e9da1991a8c9967c7f45e42/88e8799a24eb3588387e806f314e6db7/LIFELINE.pdf'
  # input_data = ["process.py", "https://trello-attachments.s3.amazonaws.com/5e9da18088805c67591114a8/5e9da1991a8c9967c7f45e42/88e8799a24eb3588387e806f314e6db7/LIFELINE.pdf",
  #                   ## ORIGINAL KEYWORDS
  #                   #  "HEMOGLOBIN","TLC","PACKED CELL VOLUME","MCV","MCH","MCHC","PLATELET COUNT","E.S.R","RBC COUNT","POLYMORPHS","LYMPHOCYTES", "EOSINOPHILS" ,"MONOCYTES","RDW","ABSOLUTE NEUTROPHIL COUNT" , "ABSOLUTE EOSINOPHIL COUNT BLOOD","FASTING GLUCOSE","MAGNESIUM","CHOLESTEROL","TRIGLYCERIDES","HDL CHOLESTEROL","LDL CHOLESTEROL ","VLDL CHOLESTEROL","HDL RATIO","LDL","UREA Serum",  "UREA NITROGEN","CREATININE SERUM","URIC ACID","SODIUM","POTASSIUM","CHLORIDE" ,"BILIRUBIN","SGOT","SGPT","ALKALINE PHOSPHATASE","TOTAL PROTEINS Serum","ALBUMIN","GLOBULIN","A:G RATIO","IgE SERUM","IRON","TIBC","UIBC","FERRITIN","FT3 Serum" ,"FREE T4","TSH"," HbA1c","VITAMIN B12","VITAMIN D","25-HYDROXY","FOLATE","INSULIN FASTING","INSULIN (PP)","BLOOD GLUCOSE PP","HOMOCYSTEINE","CRP-HS"
                    
  #                   ## MODIFIED
  #                   "HEMOGLOBIN","TLC","PACKED CELL VOLUME","MCV","MCH, Blood","MCHC","PLATELET COUNT","E.S.R","POLYMORPHS","LYMPHOCYTES", "EOSINOPHILS" ,"MONOCYTES","RDW","ABSOLUTE NEUTROPHIL COUNT" , "ABSOLUTE EOSINOPHIL COUNT BLOOD","FASTING GLUCOSE","MAGNESIUM","CHOLESTROL, SERUM","TRIGLYCERIDES","HDL CHOLESTEROL","LDL CHOLESTEROL ","VLDL CHOLESTEROL","LDL / HDL RATIO","CHOLESTEROL / HDL RATIO","LDL CHOLESTEROL","UREA Serum",  "UREA NITROGEN","CREATININE SERUM","URIC ACID","SODIUM","POTASSIUM","CHLORIDE" ,"BILIRUBIN (TOTAL)","SGOT","SGPT","ALKALINE PHOSPHATASE","TOTAL PROTEINS Serum","ALBUMIN","GLOBULIN","A:G RATIO","IgE SERUM","IRON","TIBC","UIBC","FERRITIN","FT3 Serum" ,"FREE T4","TSH, Serum"," HbA1c","VITAMIN B12","VITAMIN D, 25-HYDROXY, Serum","FOLATE, Serum","INSULIN FASTING","INSULIN PP","BLOOD GLUCOSE PP","HOMOCYSTEINE","CRP-HS",
  # #               ]

  input_data = ["process.py", "https://trello-attachments.s3.amazonaws.com/5e9da18088805c67591114a8/5e9da1991a8c9967c7f45e42/ba652b46ac8e229fc979247f8160f574/APOLLO.pdf",
        "Hemoglobin","WBC COUNT","RBC","Packed cell volume","Platelet Count","ESR","Neutrophils","Lymphocytes","Monocytes","Eosinophils","Basophils","CHOLESTEROL", "TRIGLYCERIDES", "HDL CHOLESTEROL", "LDL CHOLESTEROL","HDL CHOLESTROL RATIO","BILIRUBIN","BILIRUBIN CONJUGATED(DIRECT)","BILIRUBIN UNCONJUGATED (INDIRECT)","AST ","ALT","ALKALINE PHOSPHATASE","GGTP","ALBUMIN","GLOBULIN","ALBUMIN","FREE T3","FREE T4","TSH","HBA1C","VITAMIN B12","VITAMIN D TOTAL(250H vitD3 and 250H vitD2)","FASTING","INSULIN (PP)","HOMOCYSTEINE","CRP"
                                ]
  # input_data = ["process.py", "https://trello-attachments.s3.amazonaws.com/5e9da18088805c67591114a8/5e9da1991a8c9967c7f45e42/2c46d9f1d1a081ba10e54b1e3127bab7/MAX.pdf",
                        #  "Haemoglobin", "RBC Count", "MCV", "MCH" 
# ]


#%%
# Extracting Keywords from input_data
keywords = input_data[2:].copy()
#%%
# LEGACY CODE
del input_data[0]
pdf_url = input_data[0]
pdf_url = download_file(pdf_url)
del input_data[0]
temp_value = 100
temp_unit = "g/pl"
result_list = []
#%%
# Read the pdf and extract sentences
file = pdf_url

def main(file_path, keyword=None):
  input_data = ['mean corp hb ( mch)', 'absolute neutrophils', 'mean corp hb conc', 'folate, serum', 'eosinophil', '(glycated hba1c)/ hba1c', 'hdl cholesterol', 'esr', 'fasting', 'tsh, serum', 'lh', 'blood sugar', 'urea nitrogen', 'total proteins serum', 'red blood cell count', 'glycosylate d hemoglobin', 'serum g. o. t./ast', 'total protein', 'rdw', 'absolute eosinophil count blood', 'serum triglycerides', 'serum potassium', 'free t3', 'fsh', 'sgpt', 'sodium', 'serum cholestrol', 'cho / hdl cholesterol ratio', 'ferritin', '25-hydroxy, vitamin d', 'iron', 'neutrophil', 'neutrophils', 'triglycerides', 'estradiol', 'ldl cholesterol', 'serum sodium', 'hdl cholestrol ratio', 'tri-iodo thyroxine', 'packed cell volume', 'hematocrit', 'bilirubin', 'cholestrol, serum', 'vldl cholesterol', 'serum g. p. t. /alt', 'sgpt - alanine transaminas e', 'hba1c', 'alkaline phosphatase', 'packed cells ume', 'glucose', 'mcv', 'absolute monocytes', 'e.s.r.', 'bilirubin (indirect )', 'hemoglobin', 'blood urea nitrogen', 'chloride', 'mean corp volume', 'erythrocyte sedimentation rate', 'magnesium', 'sgot- asparttate transaminas e', 'a:g ratio', 'bilirubin unconjugated (indirect)', 'bilirubin (total)', 'total leucocytes count', 'ft3 serum', 'polymorphs', 'basophil', 'blood glucose pp', 'serum uric acid', 'serum vldl', 'mch', 'vitamin d3 level', 'rbc count', 'blood urea', 'uric acid', 'albumin', 'monocytes', 'tibc', 'eosinophils', 'serum alkaline phosphatase', 'tsh', 'alt', 'potassium', 'fasting glucose', 'mch, blood', 'rbc', 'serum l.d.l.cholestrol', 'lymphocyte', 'absolute neutrophil count', 'serum bilirubin', 'bilirubin conjugated(direct)', 'ige serum', 'serum albumin', 'vitamin d total(250h vitd3 and 250h vitd2)', 'serum tsh', 'ldl / hdl ratio', 'absolute basophils', 'free t4', 'uibc', 'e.s.r', 'cholesterol / hdl ratio', 'insulin fasting', 'serum creatinine', 'lymphocytes', 'pcv', 'mpv', 'tlc', 'sgot', 'white blood cell count', 'ggtp', 'platelets count', 'globulin', 'wbc count', 'urea serum', 'gamma g.t.', 'platelet count', 'calcium', 'cholesterol', 'insulin pp', 'bilirubin (direct)', 'basophils', 'ast', 'haemoglobin', 'folate', 'ldl / hdl cholesterol ratio', 'vitamin b12', 'vitamin d, 25-hydroxy, serum', 'insulin (pp)', 'mchc', 'creatinine serum', 'absolute lymphocytes', 'monocyte', 'vitamin b-12 level']
  input_data += ['HAEMOGLOBIN', 'TOTAL LEUCOCYTE COUNT (WBC)', 'RED BLOOD CELL COUNT', 'PACKED CELL VOLUME( HEMATOCRIT)', 'MEAN CORPUSCULAR VOLUME (MCV)', 'MEAN CORPUSULAR HB (MCH)', 'MEAN CORPUSULAR HB CONC (MCHC)', 'MEAN PLATELETS VOLUME (MPV )', 'HEMOGLOBIN DISTRIBUTION WIDTH (HDW)', 'CORPUSCULAR HAEMOGLOBIN', 'CHCM', 'PLATELET DISTRIBUTION WIDTH(PDW)', 'PCT', 'PLATELET COUNT', 'ESR', 'NEUTROPHILS %', 'LYMPHOCYTES %', 'MONOCYTES %', 'EOSINOPHILS %', 'BASOPHILS %', 'LARGE UNSTAINED CELLS (LUC)', 'RED CELL DISTRIBUTION WIDTH (RDW-CV)', 'RDW-SD', 'NEUTROPHILS', 'LYMPHOCYTES', 'MONOCYTES', 'ABSOLUTE EOSINOPHILS COUNT  %', 'BASOPHILS', 'CHOLESTEROL', 'TRIGLYCERIDES', 'H.D.L. CHOLESTEROL', 'L.D.L. CHOLESTEROL (DIRECT)', 'SERUM VLDL CHOLESTEROL', 'NON H.D.L. CHOLESTEROL', 'SERUM CHOLESTEROL-HDL RATIO', 'LDL/HDL CHOLESTEROL RATIO', 'UREA', 'BLOOD UREA NITROGEN (BUN)', 'CREATININE, SERUM', 'URIC ACID', 'UREA / CREATININE RATIO', 'BUN / CREATININE RATIO', 'CYSTATIN C', 'BLOOD KETONE', 'IONIZED CALCIUM', 'TOTAL CALCIUM', 'ZINC, SERUM', 'MERCURY', 'CAESIUM', 'BERYLLIUM', 'ARSENIC', 'PHOSPHORUS', 'SODIUM', 'POTTASIUM', 'CHLORIDE', 'MAGNESIUM', 'BILIRUBIN (TOTAL)', 'BILIRUBIN (DIRECT)', 'BILIRUBIN (INDIRECT)', 'S.G.O.T.', 'S.G.P.T.', 'ALKALINE PHOSPHATASE', 'G.G.T.P.', 'IRON SERUM', 'SERUM TOTAL PROTEINS', 'SERUM ALBUMIN', 'SERUM GLOBULIN', 'GLOBULIN', 'PANCREATIC ALFA AMYLASE', 'C.P.K.', 'IMMUNOGLOUBLIN lgG, SERUM', 'IMMUNOGLOUBLIN lgM, SERUM', 'IMMUNOGLOUBLIN lgE, SERUM', 'IMMUNOGLOUBLIN lgA, SERUM', 'IRON', 'TOTAL IRON BINDING CAPACITY (TIBC)', 'TRANSFEERRIN', 'TRANSFERRIN SATURATION', 'UNSATURATED IRON BINDING CAPACITY (UIBC)', 'FERRITIN, SERUM', 'TRANSFERRIN', 'FREE TRIJODOTHYRONINE [FT3],Serum', 'FREE THYROXINE [FT4],Serum', 'T.S.H.[ULTRA]', 'ANTI- THYROGLOBULIN ANTIBODIES', 'ANTI- THYROID PEROXIDASE', 'TESTOSTERONE LEVEL (TOTAL)', 'ESTRADIOL LEVEL', 'CORTISOL LEVEL(Morning)', 'ENHANCED ESTRADIOL ( eE2)', 'PARATHYROID HORMONE LEVEL , SERUM', 'VITAMIN B-12 LEVEL, SERUM(ECLIA)', 'VITAMIN D-3 LEVEL, SERUM (ECLIA)', 'VITAMIN D', 'FOLIC ACID LEVEL', '25-OH VITAMIN D', 'FOLATE', 'AVG SUGAR', 'BLOOD GLUCOSE (FASTING)', 'HBA1C', 'MEAN PLASMA GLUCOSE', 'INSULIN LEVEL ( FASTING ) PLASMA', 'INSULIN LEVEL ( POSTPRANDOIAL ) PLASMA', 'AVERAGE BLOOD GLUCOSE (ABG)', 'LIPASE', 'FASTING BLOOD SUGAR']
  input_data = [item.name for item in AlternateLabel.objects.all()] 
  print('888888888888888'*100)
  print('we are using this input Data', input_data)
  input_data = list(set(input_data))
  text = textract.process(file_path, method="tesseract")
  decoded_text = text.decode('utf-8')
  with open('out_to_read.txt', 'w') as writefile:
    writefile.write(decoded_text)

  # Reading out_to_read.txt line by line and saving to my_test list
  my_text = []
  with open('out_to_read.txt', 'r') as readfile:
    for line in readfile:
      my_text.append(line.lower().strip())
  #%%
  if DEBUG:
    with open('out.txt', 'w') as writefile:
      writefile.write(text.decode('utf-8'))

  result_list = []
  #%%
  for keyword in input_data:

    # read the keyword from pdf data
    # keyword_list = keyword.split(",")
    #main_key = keyword_list[0]

    value_found = ""
    unit = ""

    # for keywrd in keyword_list:
    for keywrd in [keyword]:
      
      # replacing keyword for the cases when we know for the fact that
      # that particular keyword in being read wrong in the document
      # example : converting (Glycated HbA1c)/ HbAIc  to (Glycated HbA1c)/ HbA1c
      # since this keyword is always read wrong. (not perfect but something!!) 
      # REMEMBEr : this name will be changed to normal before sending response
      original_keywrd = keyword
      keywrd = replace_wrong_read_name(keywrd, wrong_names)

      main_key = keywrd
      tag = keywrd
      input_tag = tag
      tag = tag.lower()
      tag_exist = False
      for sent in my_text:
        
        # remving .(period) from last of the sentence if present.
        if sent.endswith('.'):
          sent = sent[:-1]

        sent = sent.lower()
        tag = tag.lower()

        # if tag in sent:
        if sent.startswith(tag):
          
          # finding if there is any refrence of tag in present line
          index = sent.find(tag)

          second_half_of_line = sent[index + len(tag):].strip()

          # find if there is any xx.xx type number after keyword
          # assuming there is always .0 at the end of value
          line = re.search('(\d+(\.\d+)?)|(\.?\d+)|(\,?\d+)',second_half_of_line)
          
          # if there is no floating point number in line then line is useless
          if line is None: 
            continue

          try:
            # value_found = re.search('(\d+(\,\d+)?)|(\d+(\.\d+)?)|(\.?\d+)', second_half_of_line).group(0)
            value_found = re.search('(\d+(\.\d+)?)|(\.?\d+)', second_half_of_line).group(0)

            # Discription of idea for handling units
            # there could be units with space like '/cu mm', to handle those
            # find all the units from units_list that are present in present line
            # save them to set, convert set to list, split each item in list based on ' '
            # now I am assuming that this will contain all the possible units pattern | (ambgious)
            # now split the string based on ' ', convert to set, and get common element between
            # available_units set (previous set) and temp_unit_list (present set)
            # !! MUST HAVE : SET MUST MAINTAIN ITS ORDERING
            # keeping the ordering, convert set to list, and list to string


            # find all units from unit_list that are in seconod_half_of_line and add them to set
            available_units = set()
            for unit in units_list:
              if unit in second_half_of_line:
                available_units.add(unit)

            # separating units based on ' ' 
            try:
              available_units = [unit.split(' ') for unit in available_units ]
              available_units = [unit for item in available_units for unit in item]
            except Exception as e:
              pass
            temp_unit_list = second_half_of_line.split(" ") # /cu mm => "/cu" "mm"
            a_list = list(map(str.lower, available_units)) 
            b_list = list(map(str.lower, temp_unit_list)) 
            union_list = [unit for unit in a_list if unit in b_list]
            if len(union_list)>0:
              unit = ' '.join(union_list)
            else: 
              unit = "NA" 
            if unit == '1043/1' or unit == 'x103/pl' or unit == 'x':
              mu = u'\u03bc'   
              unit = '10^3/'+mu+'I'
          except Exception as e:
            pass
          
          try:   
            # modifing units which are known to be read wrong like emm -> cmm
            # and updating sentence
            unit, second_half_of_line = replace_wrong_read_units(unit, wrong_units, second_half_of_line)

            # reverting back to the original keywrd that was changed earlier
            main_key = original_keywrd
            
            # saving response
            temp_response = {"name":main_key.lower(), "Value":value_found.lower(), "Unit":unit.lower(), "ReadIndex":second_half_of_line.lower(), "TempSent":second_half_of_line.lower()}
            result_list.append(temp_response)
            tag_exist = True
          except Exception as e:
            pass
          unit = None


  result_data = {}
  result_data["Response"] = {"Result":result_list}

  # filtering out invalid response
  result_data = clean_response(result_data)
  return json.dumps(result_data, ensure_ascii=False)
  # print(json.dumps(result_data, ensure_ascii=False))
  # if DEBUG:
  #   print('expected output len', len(input_data))

if __name__=="__main__":
  # if DEBUG:
  #   with open('APOLO_NOW.json', 'w') as writefile:
  #     json.dump(result_data, writefile)
  # a = main('document.pdf', )
  # print(a)
  pass