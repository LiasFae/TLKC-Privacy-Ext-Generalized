import json

class Generalizer():

    def __init__(self, log):
        self.log = log

    def generalize_traces(self, logsimple, suppression_set):
        max_removed = 0
        #here
        with open("generalization_config.json", "r") as f:
            config = json.load(f)


        for key in logsimple.keys():
            count_removed = 0
            list_trace = logsimple[key]['trace']
            generalized_traces = generalize(list_trace, config, suppression_set)
            # for i, (event, count) in enumerate(list_trace):
            #     if (event, count) in suppression_set:
            #         event_path = event.split(":")
                    # sub_config = config[event_path[0]]
                    # for node in event_path[1:]:
                    #     if node not in sub_config:
                    #         break
                    #     sub_config = sub_config[node]
                    # generalized_event = ":".join(list(sub_config.keys())[0].split(":")[:-1])
                    # list_trace[i] = (generalized_event, count)
            logsimple[key]['trace'] = generalized_traces
        return logsimple, max_removed

def generalize_event(event, config):
    event_type = None
    if ":" in event[0]:
        event_path = event[0].split(":")
        try:
            sub_config = config[event_path[0]]
        except KeyError:
            raise ValueError(f"Key {event_path[0]} not found in config.")
        for path in event_path[1:]:
            try:
                sub_config = sub_config[path]
            except KeyError:
                raise ValueError(f"Key {path} not found in config.")
        event_type = list(sub_config.keys())[0]
    else:
        event_type = list(config.keys())[0]
    return (event_type, event[1])


def update_trace(trace, old_event, new_event):
    updated_trace = []
    if trace == old_event:
        updated_trace.append(new_event)
    else:
        updated_trace.append(trace)
    return updated_trace


def generalize(list_trace, config, violating_list):
    for i, trace in enumerate(list_trace):
        for violating_event in violating_list:
            if violating_event == trace:
                generalized_event = generalize_event(violating_event, config)
                updated_trace = update_trace(trace, violating_event, generalized_event)
                list_trace[i] = updated_trace
    return list_trace