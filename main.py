from datetime import datetime
from p_tlkc_privacy_ext.privacyPreserving import privacyPreserving
import pandas as pd
from pm4py.objects.log.importer.xes import factory as xes_import_factory
from pm4py.objects.conversion.log import factory as conversion_factory
import os

if __name__ == '__main__':
    event_log = "Sepsis-Cases-Case-attributes.xes"
    xes_log = xes_import_factory.apply(event_log)
    csv_log = conversion_factory.apply(xes_log, variant=conversion_factory.TO_DATAFRAME)
    csv_file_path = os.path.join('./xes_results', 'Sepsis-Cases-Case-attributes.csv')
    csv_log.to_csv(csv_file_path, index=False, sep=',', encoding='utf-8')

    L = [2]
    K = [20]
    C = [0.5]
    alpha = 0.5  # privacy coefficent
    beta = 0.5  # utility coefficent
    event_in_log = 0.5
    event_in_variant = 0.5
    utility_measure = [event_in_log,event_in_variant]
    sensitive_att = ['Diagnose']  # categorical sensitive attributes
    T = ["minutes"]  # original, seconds, minutes, hours, days
    generalising = False # True to use a generalization approach, False for suppression
    method = "suppressed" # generalized or suppressed
    cont = []  # numerical sensitive attributes
    bk_type = "set"  # set, multiset, sequence, relative
    event_attributes = ['concept:name']  # to simplify the event log
    life_cycle = ['complete', '', 'COMPLETE']  # these life cycles are applied only when all_lif_cycle = False
    all_life_cycle = True  # when life cycle is in trace attributes then all_life_cycle has to be True
    pa_log_dir = "./xes_results"
    pa_log_name = event_log[:-4]
    multiprocess = True  # if you want to you use multiprocessing
    mp_technique = 'pool'
    if not os.path.exists(pa_log_dir):
        os.makedirs(pa_log_dir)
    pp = privacyPreserving(event_log)
    privacy_aware_log_dir, max_removed = pp.apply(T, L, K, C, sensitive_att, cont, generalising, bk_type, event_attributes, life_cycle, all_life_cycle,
                                   alpha, beta, pa_log_dir, pa_log_name, False, utility_measure=utility_measure, multiprocess=multiprocess, mp_technique=mp_technique)
    print(privacy_aware_log_dir)

    # subtract the logs

    df1 = pd.read_csv("./xes_results/Sepsis-Cases-Case-attributes.csv")
    df2 = pd.read_csv("./xes_results/Sepsis-Cases-Case-attributes_minutes_2_20_0.5_" + bk_type + "_" + method + ".csv")
    
    key_cols = ["InfectionSuspected","org:group","SIRSCritTachypnea","Hypotensie","SIRSCritHeartRate","Infusion","DiagnosticArtAstrup","concept:name","DiagnosticIC","DiagnosticSputum","DiagnosticLiquor","DiagnosticOther","SIRSCriteria2OrMore","DiagnosticXthorax","SIRSCritTemperature","DiagnosticUrinaryCulture","SIRSCritLeucos","Oligurie","DiagnosticLacticAcid","lifecycle:transition","Hypoxie","DiagnosticUrinarySediment","DiagnosticECG","case:concept:name","case:DiagnosticBlood","case:DisfuncOrg","case:Age","case:Diagnose","Leucocytes","CRP","LacticAcid"] 
    # leaves out "time:timestamp"

    df1 = df1[~df1.duplicated(subset=df1.columns.difference(['time:timestamp']).tolist())]

    df = pd.concat([df1, df2]).drop_duplicates(subset=df1.columns.difference(['time:timestamp']).tolist(), keep=False)

    df.to_csv('./xes_results/removed_rows_' + bk_type + '.csv', index=False)