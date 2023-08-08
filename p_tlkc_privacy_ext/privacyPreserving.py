from datetime import datetime
from pm4py.objects.log.importer.xes import factory as xes_importer_factory
from pm4py.objects.log.exporter.xes import factory as xes_exporter
import pandas as pd
from pm4py.objects.conversion.log import factory as conversion_factory
from p_privacy_metadata.privacyExtension import privacyExtension
from p_tlkc_privacy_ext import Anonymizer
from p_tlkc_privacy_ext import FileConverter
import os

class privacyPreserving(object):
    '''
    Applying privacy preserving technique
    '''

    def __init__(self, log):
        '''
        Constructor
        '''
        self.log = xes_importer_factory.apply(log)

    def apply(self, T, L, K, C, sensitive_att, cont, generalising, generalization_type, generalising_max_iterations, gen_config, bk_type, trace_attributes, life_cycle, all_life_cycle, alpha, beta, directory, file_name, external_name, utility_measure=[0.5,0.5], multiprocess=True, mp_technique='pool'):
        if bk_type == 'relative':
            dict1 = {
                l: {k: {c: {t: {"w": [], "x": [], "v": []} for t in T} for c in C} for k in K}
                for l in range(0, L[len(L) - 1] + 1)}
        else:
            dict1 = {
                l: {k: {c: {"w": [], "x": [], "v": []} for c in C} for k in K}
                for l in range(0, L[len(L) - 1] + 1)}

        anonymizer = Anonymizer.Anonymizer()
        privacy_aware_log_dir = ""
        exception_msg = "An exception happend!"
        for l in L:
            print("l = " + str(l) + " is running...")
            for k in K:
                for c in C:
                    try:
                        if bk_type == "set" or bk_type == "multiset" or bk_type == "sequence":
                            print("l = " + str(l) + " type = " + str(bk_type) + " is running...")
                            log2 = {t: None for t in T}
                            for t in T:
                                log2[t] = self.log
                            log, violating_length, d, d_l, dict2, max_removed = \
                                anonymizer.none_relative_type(self.log, log2, sensitive_att, cont, l, L, k, K, c, C, dict1, T,
                                                              trace_attributes, life_cycle, all_life_cycle, generalising, 
                                                              generalization_type, generalising_max_iterations, gen_config, bk_type, alpha, beta,
                                                              utility_measure, multiprocess, mp_technique)
                            dict1 = dict2
                            for t in T:
                                self.add_privacy_metadata(log[t])
                                if external_name:
                                    privacy_aware_log_dir = os.path.join(directory, file_name)
                                else:
                                    if generalising:
                                        n_file_path = file_name + "_" + str(t) + "_" + str(l) + "_" + str(k) + "_" + str(
                                            c) + "_" + bk_type + "_generalized_" +  generalization_type + ".xes"
                                    else:
                                        n_file_path = file_name + "_" + str(t) + "_" + str(l) + "_" + str(k) + "_" + str(
                                            c) + "_" + bk_type + "_suppressed.xes"                                        
                                    privacy_aware_log_dir = os.path.join(directory, n_file_path)
                                xes_exporter.export_log(log[t], privacy_aware_log_dir)

                                if generalising:
                                    n_file_path_csv = file_name + "_" + str(t) + "_" + str(l) + "_" + str(k) + "_" + str(c) + "_" + bk_type + "_generalized_" +  generalization_type + ".csv"
                                else:
                                    n_file_path_csv = file_name + "_" + str(t) + "_" + str(l) + "_" + str(k) + "_" + str(c) + "_" + bk_type + "_suppressed.csv"
 

                                fileConverter = FileConverter.FileConverter()
                                fileConverter.convert_to_csv(log[t], n_file_path_csv, directory)

                                print(n_file_path + " has been exported!")
                        # functionality for bk_type relative
                        elif bk_type == "relative":
                            print("l = " + str(l) + " type = " + str(bk_type) + " is running...")
                            for t in T:
                                log_time, violating_length_time, d_time, d_l_time, dict2, max_removed = \
                                    anonymizer.relative_type(self.log, sensitive_att, cont, t, l, k, c, dict1,
                                                             trace_attributes, life_cycle, all_life_cycle, bk_type,
                                                             alpha, beta, utility_measure, multiprocess, mp_technique)
                                self.add_privacy_metadata(log_time)
                                if external_name:
                                    privacy_aware_log_dir = os.path.join(directory, file_name)
                                else:
                                    n_file_path = file_name + "_" + str(t) + "_" + str(l) + "_" + str(k) + "_" + str(
                                    c) + "_" + bk_type + ".xes"
                                    privacy_aware_log_dir = os.path.join(directory, n_file_path)
                                xes_exporter.export_log(log_time, privacy_aware_log_dir)

                                n_file_path_csv = file_name + "_" + str(t) + "_" + str(l) + "_" + str(k) + "_" + str(c) + "_" + bk_type + ".csv"

                                fileConverter = FileConverter.FileConverter()
                                fileConverter.convert_to_csv(log_time, n_file_path_csv, directory)

                                print(n_file_path + " has been exported!")
                                dict1 = dict2
                    except Exception as e:
                        exception_msg = e
                        print(e)

        if privacy_aware_log_dir != "":
            return privacy_aware_log_dir, max_removed
        else:
            return exception_msg


    def add_privacy_metadata(self, log):
        prefix = 'privacy:'
        uri = 'paper_version_uri/privacy.xesext'

        privacy = privacyExtension(log, prefix, uri)
        privacy.set_anonymizer('suppression', 'event', 'event')
