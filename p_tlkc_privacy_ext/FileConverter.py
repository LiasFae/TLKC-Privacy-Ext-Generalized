from pm4py.objects.log.importer.xes import factory as xes_importer_factory
from pm4py.objects.log.exporter.xes import factory as xes_exporter
import pandas as pd
import os
from pm4py.objects.conversion.log import factory as conversion_factory

class FileConverter:

    def __init__(self):
        self = self

    def convert_to_csv(self, eventLog, fileName, directory):
        csv_file_path = os.path.join(directory, fileName)
        csv_log = conversion_factory.apply(eventLog, variant=conversion_factory.TO_DATAFRAME)
        csv_log.to_csv(csv_file_path, index=False, sep=',', encoding='utf-8')
        print(fileName + " has been exported!")
        return csv_log