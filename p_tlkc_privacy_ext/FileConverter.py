from pm4py.objects.log.importer.xes import factory as xes_importer_factory
from pm4py.objects.log.exporter.xes import factory as xes_exporter
import pandas as pd
import os
from pm4py.objects.conversion.log import factory as conversion_factory
import csv

class FileConverter:

    def __init__(self):
        self = self

    def convert_to_csv(self, eventLog, fileName, directory):
        csv_file_path = os.path.join(directory, fileName)
        csv_log = conversion_factory.apply(eventLog, variant=conversion_factory.TO_DATAFRAME)
        csv_log.to_csv(csv_file_path, index=False, sep=',', encoding='utf-8')
        print(fileName + " has been exported!")
        return csv_log
    
    def convert_to_csv2(self, eventLog, fileName, directory):
        csv_file_path = os.path.join(directory, fileName)
        # open a file for writing
        with open(csv_file_path, 'w', newline='') as file:
            writer = csv.writer(file)

            # write the header row
            writer.writerow(eventLog.keys())

            # write the values row by row
            for row in zip(*eventLog.values()):
                writer.writerow(row)
    
    def create_csv_file_for_traces(traces, file_name):
        # Open the file in write mode with newline=''
        with open(file_name, 'w', newline='') as file:
            writer = csv.writer(file)

            # Write the header row
            writer.writerow(['trace_id', 'event_name', 'event_time', 'lifecycle_transition'])

            # Write the data rows
            for trace_id, trace in enumerate(traces):
                for event_index, event in enumerate(trace):
                    event_name = event['concept:name']
                    event_time = event['time:timestamp']
                    lifecycle_transition = event.get('lifecycle:transition', '')
                    writer.writerow([trace_id, event_name, event_time, lifecycle_transition])            