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

    #TODO: für Multiset muss eine Prüfung stattfinden, ob das Event < k ist, auch ohne die Occurence, da sonst
    # durch die Prüfung gegen L Events durchrutschen können, die kleiner k sind

    L = [2] #strength of background knowledge, for multiset adversary only knows 
    K = [20]
    C = [0.5]
    alpha = 0.5  # privacy coefficent
    beta = 0.5  # utility coefficent
    event_in_log = 0.5
    event_in_variant = 0.5
    utility_measure = [event_in_log,event_in_variant]
    sensitive_att = ['Diagnose']  # categorical sensitive attributes
    T = ["minutes"]  # original, seconds, minutes, hours, days
    generalising = True # True to use a generalization approach, False for suppression
    generalising_iterations = 2
    cont = []  # numerical sensitive attributes
    bk_type = "multiset"  # set, multiset, sequence, relative
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
    
    if generalising:
        for i in range(generalising_iterations):
            event_log_gen = "xes_results/Sepsis-Cases-Case-attributes_" + str(T[0]) + "_" + str(L[0]) + "_" + str(K[0]) + "_" + str(C[0]) + "_" + bk_type + "_generalized.xes"
            pa_log_name_gen = event_log[:-4]
            pp_gen = privacyPreserving(event_log_gen)
            privacy_aware_log_dir, max_removed = pp_gen.apply(T, L, K, C, sensitive_att, cont, generalising, bk_type, event_attributes, life_cycle, all_life_cycle,
                                        alpha, beta, pa_log_dir, pa_log_name_gen, False, utility_measure=utility_measure, multiprocess=multiprocess, mp_technique=mp_technique)
            
    # subtract the logs
    if generalising:
        method = "generalized"
    else:
        method = "suppressed"
        df1 = pd.read_csv("./xes_results/Sepsis-Cases-Case-attributes.csv")
        df2 = pd.read_csv("./xes_results/Sepsis-Cases-Case-attributes_minutes_2_20_0.5_" + bk_type + "_" + method + ".csv")   
        key_cols = ["InfectionSuspected","org:group","SIRSCritTachypnea","Hypotensie","SIRSCritHeartRate","Infusion","DiagnosticArtAstrup","concept:name","DiagnosticIC","DiagnosticSputum","DiagnosticLiquor","DiagnosticOther","SIRSCriteria2OrMore","DiagnosticXthorax","SIRSCritTemperature","DiagnosticUrinaryCulture","SIRSCritLeucos","Oligurie","DiagnosticLacticAcid","lifecycle:transition","Hypoxie","DiagnosticUrinarySediment","DiagnosticECG","case:concept:name","case:DiagnosticBlood","case:DisfuncOrg","case:Age","case:Diagnose","Leucocytes","CRP","LacticAcid"] 
        # leaves out "time:timestamp"
        df1 = df1[~df1.duplicated(subset=df1.columns.difference(['time:timestamp']).tolist())]
        df = pd.concat([df1, df2]).drop_duplicates(subset=df1.columns.difference(['time:timestamp']).tolist(), keep=False)
        df.to_csv('./xes_results/removed_rows_' + bk_type + '_' + method +'.csv', index=False)