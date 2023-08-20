import json
import operator
import datetime
import csv
from pm4py.objects.log.log import Trace, EventLog
from pm4py.objects.log.util import sorting
from collections import Counter
from multiset import Multiset
from dateutil.relativedelta import relativedelta
from calendar import monthrange
from p_tlkc_privacy_ext import FileConverter, Generalizer
import copy

class ELReps():

    def __init__(self, log):
        # log = sorting.sort_timestamp(log)
        self.log = log

    def create_simple_log(self, bk_type, trace_attributes, life_cycle, all_life_cycle, sensitive_attributes,time_accuracy): #time_accuracy
        time_prefix = ['time:timestamp']
        life_cycle_prefix = ['lifecycle:transition']
        logsimple = {}
        traces = []
        sensitives = {el: [] for el in sensitive_attributes}

        for case_index, case in enumerate(self.log):
            trace, sens = self.create_trace(case,trace_attributes,life_cycle,all_life_cycle,life_cycle_prefix,time_prefix,bk_type,sensitive_attributes,time_accuracy,False)
            logsimple[case.attributes["concept:name"]] = {"trace":  trace, "sensitive": sens}
            traces.append(trace)
            # sample all values for a specific sensitive attribute (key) in dict
            for key in sens.keys():
                # sample all values for a specific sensitive attribute (key) in dict
                sensitives[key].append(sens[key])
        return logsimple, traces, sensitives

    def get_multiset_log(self,alist):
        mult_log = []
        alist_tuple = tuple(alist)
        for s in set(alist):
            count = alist_tuple.count(s)
            tu = (s,count)
            mult_log.append(tu)
        return mult_log

    def get_multiset_log_n(self,alist):
        mult_log = []
        for s in alist:
            mult_log.append(Multiset(s))
        return mult_log

    def suppression(self, violating, frequent, relative_freq,alpha, beta):
        sup = []
        X1 = []
        for v in violating + frequent:
            if isinstance(v[0], str):
                X1.append(v)
            else:
                for sub in v:
                    X1.append(sub)
        X1 = list(set(X1))
        # score_res, mvsEl, mfsEl = self.score(violating, frequent, X1)
        score_res, mvsEl, mfsEl = self.new_score(violating, frequent, X1, relative_freq,alpha, beta)

        # while PG table is not empty do
        while len(violating) > 0:
            # 4: select a pair w that has the highest Score to suppress;
            w = max(score_res.items(), key=operator.itemgetter(1))[0]
            # 5: delete all MVS and MFS containing w from MVS -tree and MFS - tree;
            list_mvs = mvsEl[w]
            for l in list_mvs:
                if l not in violating:
                    pass
                    # print(l)
                    # print(violating)
                else:
                    violating.remove(l)
            list_mfs = mfsEl[w]
            for l in list_mfs:
                frequent.remove(l)
            # 6: update the Score(p) if both w and p are contained in the same MVS or MFS;
            X1 = []
            for v in violating + frequent:
                if isinstance(v[0], str):
                    X1.append(v)
                else:
                    for sub in v:
                        X1.append(sub)
            X1 = list(set(X1))
            if len(violating) > 0:
                # 7: remove w from PG Table;
                # score_res, mvsEl, mfsEl = self.score(violating, frequent, X1)
                score_res, mvsEl, mfsEl = self.new_score(violating, frequent, X1, relative_freq,alpha, beta)
            # 8: add w to Sup;
            sup.append(w)
        # 9: end
        return sup

    def suppression_new(self, violating, relative_freq, alpha, beta, generalising, gen_config):
        # --- Generalizer Add-On ---
        if generalising:
            with open(gen_config, "r") as f:
                config = json.load(f)
            top_node = next(iter(config.keys()))
        else:
            top_node = ''
        # --- Generalizer Add-On End ---  
        sup = []
        X1 = []
        for v in violating:
            if isinstance(v[0], str):
                X1.append(v)
            else:
                for sub in v:
                    X1.append(sub)
        X1 = list(set(X1))
        # score_res, mvsEl, mfsEl = self.score(violating, frequent, X1)
        # --- Generalizer Add-On ---
        if generalising:
            score_res, mvsEl = self.new_score2(violating, X1, relative_freq, alpha, beta, top_node)
        else:
        # --- Generalizer Add-On End ---  
            score_res, mvsEl = self.new_score2(violating, X1, relative_freq, alpha, beta, '')
        # while PG table is not empty do
        while len(violating) > 0:
            # 4: select a pair w that has the highest Score to suppress;
            w = max(score_res.items(), key=operator.itemgetter(1))[0]
            # 5: delete all MVS and MFS containing w from MVS -tree and MFS - tree;
            list_mvs = mvsEl[w]
            for l in list_mvs:
                if l not in violating:
                    pass
                    # print(l)
                    # print(violating)
                else:
                    violating.remove(l)
            # 6: update the Score(p) if both w and p are contained in the same MVS or MFS;
            X1 = []
            for v in violating:
                if isinstance(v[0], str):
                    X1.append(v)
                else:
                    for sub in v:
                        X1.append(sub)
            X1 = list(set(X1))
            if len(violating) > 0:
                # 7: remove w from PG Table;
                # score_res, mvsEl, mfsEl = self.score(violating, frequent, X1)
                # --- Generalizer Add-On ---
                if generalising:
                    score_res, mvsEl = self.new_score2(violating, X1, relative_freq, alpha, beta, top_node)
                else:
                # --- Generalizer Add-On End --- 
                    score_res, mvsEl = self.new_score2(violating, X1, relative_freq, alpha, beta, '')
            # 8: add w to Sup;
            # --- Generalizer Add-On --- 
            if w[0] == top_node:
                continue
            else:
            # --- Generalizer Add-On End ---         
                sup.append(w)
        # 9: end
        return sup

    def update_score(self,scores,mvsEl):
        updated_scores = {}
        all_elem = [sublist for sublist in mvsEl]
        all_elem_set = set(all_elem)
        for key,value in scores.items():
            affected_elem = self.get_unique_elment_list(key, mvsEl)
            updated_scores[key] = value + len(affected_elem) / len(all_elem_set)
        return updated_scores

    def get_freq_list(self,list,relative_freq):
        flat_list = [item for sublist in list for item in sublist]
        flat_list_set = set(flat_list)
        sum_freq = 0
        for item in flat_list_set:
            sum_freq += relative_freq[item]
        return sum_freq

    def get_unique_elment_list(self,el, mvsEl):
        list_elem =[]
        for key,value in mvsEl.items():
            if key == el:
                list_elem.append(value)

        flat_list = [item for sublist in list_elem[0] for item in sublist]
        flat_list_set = set(flat_list)
        return flat_list_set

    def score(self,violating, frequent, X1, relative_freq):
        priv = {v: 0 for v in X1}
        ut = {f: 0 for f in X1}
        mvsEle = {v: [] for v in X1}
        mfsEle = {f: [] for f in X1}
        for v in violating:
            if isinstance(v[0], str):
                priv[v] += 1
                mvsEle[v].append(v)
            else:
                for el in v:
                    priv[el] += 1
                    mvsEle[el].append(v)
        for f in frequent:
            if isinstance(f[0], str):
                ut[f] += 1
                mfsEle[f].append(f)
            else:
                for el in f:
                    ut[el] += 1
                    mfsEle[el].append(f)
        score = {el: 0 for el in X1}
        for el in X1:
            if ut[el] == 0:
                score_val = priv[el] + (1 - relative_freq[el])
            else:
                score_val = priv[el] / (ut[el] + 1)
            score[el] = score_val
            if score[el] == 0:
                del score[el]

        return score, mvsEle, mfsEle

    def new_score(self,violating, frequent, X1, relative_freq,alpha, beta): #consider relative frequencies as well as MFT
        priv = {v: 0 for v in X1}
        ut = {f: 0 for f in X1}
        mvsEle = {v: [] for v in X1}
        mfsEle = {f: [] for f in X1}
        for v in violating:
            if isinstance(v[0], str):
                priv[v] += 1
                mvsEle[v].append(v)
            else:
                for el in v:
                    priv[el] += 1
                    mvsEle[el].append(v)
        for f in frequent:
            if isinstance(f[0], str):
                ut[f] += 1
                mfsEle[f].append(f)
            else:
                for el in f:
                    ut[el] += 1
                    mfsEle[el].append(f)
        score = {el: 0 for el in X1}
        for el in X1:
            privacy = priv[el] / len(violating)
            if ut[el] != 0:
                utility = 1 - (ut[el] / len(frequent))
            else:
                utility = (1 - relative_freq[el])**2
            if privacy == 0:
                score_val = 0
            else:
                score_val = alpha * privacy + beta * utility

            score[el] = score_val
            if score[el] == 0:
                del score[el]

        return score, mvsEle, mfsEle

    def new_score2(self,violating, X1, relative_freq,alpha, beta, top_node): #utility based on frequencies
        priv = {v: 0 for v in X1}
        mvsEle = {v: [] for v in X1}
        for v in violating:
            if isinstance(v[0], str):
                priv[v] += 1
                mvsEle[v].append(v)
            else:
                for el in v:
                    priv[el] += 1
                    mvsEle[el].append(v)

        score = {el: 0 for el in X1}
        for el in X1:
            # --- Generalizer Add-On ---
            if el[0] == top_node:
                score_val = 0.0000001
            else:
            # --- Generalizer Add-On End ---
                privacy = priv[el] / len(violating)
                utility = 1 - relative_freq[el]
                if privacy == 0:
                    score_val = 0
                else:
                    # score_val = 2 * (privacy * utility) / utility + privacy
                    score_val = alpha * privacy + beta * utility
                    # score_val = (alpha * privacy) / (beta * utility)
            score[el] = score_val
            if score[el] == 0:
                del score[el]

        return score, mvsEle

    def suppress_traces(self,logsimple, sup):
        max_removed = 0
        for key in logsimple.keys():
            count_removed = 0
            list_trace = logsimple[key]['trace']
            for i in range(len(list_trace)-1, -1, -1):
                sub = list_trace[i]
                if sub in sup:
                    list_trace.remove(sub)
                    count_removed += 1
            if count_removed > max_removed:
                max_removed = count_removed
            logsimple[key]['trace'] = list_trace
        return logsimple, max_removed

    def create_trace(self, case, trace_attributes, life_cycle, all_life_cycle, life_cycle_prefix, time_prefix, bk_type,sensitive_attributes,time_accuracy, from_create_event_log):
        sens = {}
        trace = []
        trace_temp = []
        sens_dict = {}
        for key, value in case.attributes.items():
            if key in sensitive_attributes:
                sens_dict[key] = value

        for event_index, event in enumerate(case):
            # basis for tuple of (event,time)
            simple_event = [[], []]
            simple_attr_temp = []
            life_cycle_value = ''
            event_dict = {}
            for key, value in event.items():
                # Filtering out the needed attributes and create new log out of it
                # simplify timestamp to timeintervalls as precise as spectime
                # pair[1] = time
                if bk_type == 'relative' and key in time_prefix:
                    if event_index == 0:
                        starttime = value
                        time = 0
                    else:
                        if time_accuracy == "seconds":
                            time = (value - starttime).total_seconds()
                        elif time_accuracy == "minutes":
                            time = (value.replace(second=0, microsecond=0)
                                    - starttime.replace(second=0, microsecond=0)).total_seconds() / 60
                        elif time_accuracy == "hours":
                            time = (value.replace(minute=0, second=0, microsecond=0)
                                    - starttime.replace(minute=0, second=0, microsecond=0)).total_seconds() / 360
                        elif time_accuracy == "days":
                            time = (value.replace(hour=0, minute=0, second=0, microsecond=0)
                                    - starttime.replace(hour=0, minute=0, second=0,
                                                        microsecond=0)).total_seconds() \
                                   / 8640
                # pair[0] = event
                if key in trace_attributes:
                    event_dict[key] = value
                    # simple_attr_temp.append(event_dict)
                if key in sensitive_attributes:
                    # sample all sensitive values for one trace in sens
                    sens_dict[key] = value
                if key in life_cycle_prefix:
                    # sample all sensitive values for one trace in sens
                    life_cycle_value = value
            if all_life_cycle or (life_cycle_value in life_cycle):
                if len(event_dict) < 2:
                    simple_event[0] = list(event_dict.values())[0]
                    # simple_event[0] = tuple(simple_attr_temp)[0]
                else:
                    for att in trace_attributes:
                        if att in event_dict:
                            simple_attr_temp.append(event_dict[att])
                    simple_event[0] = tuple(simple_attr_temp)
                if bk_type == 'relative':
                    simple_event[1] = time
                    tu = (simple_event[0], simple_event[1])
                elif bk_type == 'multiset':
                    tu = (simple_event[0])
                    trace_temp.append(simple_event[0])
                elif bk_type == 'sequence':  # or bk_type == 'multiset':
                    # count_event = trace_temp.count(simple_event[0])
                    # simple_event[1] = count_event + 1
                    simple_event[1] = 0
                    tu = (simple_event[0], simple_event[1])
                    trace_temp.append(simple_event[0])
                elif bk_type == 'set':
                    simple_event[1] = 0
                    tu = (simple_event[0], simple_event[1])
                trace.append(tu)

                for item in sensitive_attributes:
                    if item in sens_dict:
                        sens[item] = sens_dict[item]

        if bk_type == 'multiset' and not from_create_event_log:
            trace = self.get_multiset_log(trace)

        return trace, sens

    def createEventLog(self, simplifiedlog, generalising, replacement_list, spectime, trace_attributes,life_cycle,all_life_cycle,bk_type, sensitive_attributes, time_accuracy):
        time_prefix = ['time:timestamp']
        life_cycle_prefix = ['lifecycle:transition']
        deleteLog = []
        log = copy.deepcopy(self.log)
        d = 0
        d_l = 0
        for i in range(0, len(log)):
            caseId = log[i].attributes["concept:name"]
            if not generalising:
                if caseId not in simplifiedlog.keys():
                    deleteLog.append(i)
                    continue
            trace = simplifiedlog[caseId]["trace"]
            k = 0
            j = 0
            del_list = []
            simple_trace, sens = self.create_trace(log[i], trace_attributes, life_cycle, all_life_cycle, life_cycle_prefix,
                                            time_prefix, bk_type, sensitive_attributes, time_accuracy, True)
            starttime = 0
            time_exception_happend = 0
            while j < len(log[i]): #and k < len(trace):
                if (bk_type !='multiset' and simple_trace[j] in trace) or \
                        (bk_type =='multiset' and simple_trace[j] in [el[0] for el in trace]) or \
                        generalising :
                    # --- Generalizer Add-On --
                    if (bk_type !='multiset' and not simple_trace[j] in trace and generalising) or (bk_type =='multiset' and not simple_trace[j] in [el[0] for el in trace] and generalising):
                        replacement_el = None
                        for el in replacement_list:
                            if (bk_type == 'multiset'):
                                if el[0] == simple_trace[j]:
                                    replacement_el = el[1]
                                    break
                            else:
                                if el[0] == simple_trace[j][0]:
                                    replacement_el = el[1]
                                    break                                 
                        if replacement_el is not None and not(replacement_el == "SUPPRESS_EVENT"):
                            log[i][j]['concept:name'] = replacement_el
                        elif replacement_el == "SUPPRESS_EVENT":
                            del_list.append(log[i][j])
                    # --- Generalizer Add-On End --
                    if spectime == "seconds":
                        if starttime == 0:
                            starttime = log[i][j]['time:timestamp']
                            base_year = starttime.year
                            log[i][j]['time:timestamp'] = datetime.datetime(year=base_year, month=1, day=1,
                                                                            hour=0, minute=0, second=0)
                        else:
                            # timedif = log[i][j]['time:timestamp'] - starttime
                            # years = int(timedif.days / 365)
                            # daystime = timedif.days - years * 365
                            # month, days = self.month_translate(daystime)
                            # sectim = timedif.seconds
                            # # 60sec -> 1 min, 60*60sec -> 60 min -> 1 hour
                            # hours = int(sectim / 3600)
                            # sectim = sectim - hours * 3600
                            # minutes = int(sectim / 60)
                            # sectim = sectim - minutes * 60
                            startstr = starttime.strftime("%Y-%m-%d %H:%M:%S")
                            endstr = log[i][j]['time:timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                            start = datetime.datetime.strptime(startstr, '%Y-%m-%d %H:%M:%S')
                            ends = datetime.datetime.strptime(endstr, '%Y-%m-%d %H:%M:%S')
                            diff = relativedelta(ends, start)
                            years = diff.years
                            month = diff.months
                            days = diff.days
                            hours = diff.hours
                            minutes = diff.minutes
                            sectim = diff.seconds
                            try:
                                log[i][j]['time:timestamp'] = datetime.datetime(year=base_year + years, month=1 + month,
                                                                            day=1 + days, hour=hours,
                                                                            minute=minutes, second=sectim)
                                if time_exception_happend != 0:
                                    days += time_exception_happend.day
                                    log[i][j]['time:timestamp'] = datetime.datetime(year=base_year + years,
                                                                                    month=1 + month,
                                                                                    day=1 + days, hour=hours,
                                                                                    minute=minutes, second=sectim)
                                    if log[i][j]['time:timestamp'] < time_exception_happend:
                                        log[i][j]['time:timestamp'] = time_exception_happend

                            except:
                                daysOfmonth = monthrange(log[i][j]['time:timestamp'].year, 1 + month)[1]
                                if days + 1 > daysOfmonth:
                                    month += 1
                                    days = days - daysOfmonth + 1
                                log[i][j]['time:timestamp'] = datetime.datetime(year=base_year + years,
                                                                                month=1 + month,
                                                                                day=days, hour=hours,
                                                                                minute=minutes, second=sectim)

                    elif spectime == "minutes":
                        if starttime == 0:
                            starttime = log[i][j]['time:timestamp']
                            base_year = starttime.year
                            log[i][j]['time:timestamp'] = datetime.datetime(year=base_year, month=1, day=1,
                                                                            hour=0, minute=0,second=0)
                        else:
                            startstr = starttime.strftime("%Y-%m-%d %H:%M:%S")
                            endstr = log[i][j]['time:timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                            start = datetime.datetime.strptime(startstr, '%Y-%m-%d %H:%M:%S')
                            ends = datetime.datetime.strptime(endstr, '%Y-%m-%d %H:%M:%S')
                            diff = relativedelta(ends, start)
                            years = diff.years
                            month = diff.months
                            days = diff.days
                            hours = diff.hours
                            minutes = diff.minutes
                            sectim = diff.seconds

                            try:
                                log[i][j]['time:timestamp'] = datetime.datetime(year=base_year + years, month= 1 + month,
                                                                            day= 1 + days, hour=hours,
                                                                            minute=minutes,second=0)
                                if time_exception_happend != 0:
                                    days += time_exception_happend.day
                                    log[i][j]['time:timestamp'] = datetime.datetime(year=base_year + years,
                                                                                    month=1 + month,
                                                                                    day=1 + days, hour=hours,
                                                                                    minute=minutes, second=0)
                                    if log[i][j]['time:timestamp'] < time_exception_happend:
                                        log[i][j]['time:timestamp'] = time_exception_happend

                            except:
                                daysOfmonth = monthrange(log[i][j]['time:timestamp'].year, 1 + month)[1]
                                if days + 1 > daysOfmonth:
                                    month += 1
                                    days = days - daysOfmonth + 1
                                    log[i][j]['time:timestamp'] = datetime.datetime(year=base_year + years,
                                                                                month=1 + month,
                                                                                day=days, hour=hours,
                                                                                minute=minutes, second=0)
                                    time_exception_happend = log[i][j]['time:timestamp']

                    elif spectime == "hours":
                        if starttime == 0:
                            starttime = log[i][j]['time:timestamp']
                            base_year = starttime.year
                            log[i][j]['time:timestamp'] = datetime.datetime(year=base_year, month=1, day=1,
                                                                            hour=0,minute=0,second=0)
                        else:
                            startstr = starttime.strftime("%Y-%m-%d %H:%M:%S")
                            endstr = log[i][j]['time:timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                            start = datetime.datetime.strptime(startstr, '%Y-%m-%d %H:%M:%S')
                            ends = datetime.datetime.strptime(endstr, '%Y-%m-%d %H:%M:%S')
                            diff = relativedelta(ends, start)
                            years = diff.years
                            month = diff.months
                            days = diff.days
                            hours = diff.hours
                            minutes = diff.minutes
                            sectim = diff.seconds
                            try:
                                log[i][j]['time:timestamp'] = datetime.datetime(year=base_year + years, month=1 + month,
                                                                          day=1 + days, hour=hours,minute=0,second=0)
                                if time_exception_happend != 0:
                                    days += time_exception_happend.day
                                    log[i][j]['time:timestamp'] = datetime.datetime(year=base_year + years,
                                                                                    month=1 + month,
                                                                                    day=1 + days, hour=hours,
                                                                                    minute=0, second=0)
                                    if log[i][j]['time:timestamp'] < time_exception_happend:
                                        log[i][j]['time:timestamp'] = time_exception_happend

                            except:
                                daysOfmonth = monthrange(log[i][j]['time:timestamp'].year, 1 + month)[1]
                                if days + 1 > daysOfmonth:
                                    month += 1
                                    days = days - daysOfmonth + 1
                                log[i][j]['time:timestamp'] = datetime.datetime(year=base_year + years,
                                                                                month=1 + month,
                                                                                day= days, hour=hours, minute=0,
                                                                                second=0)
                    elif spectime == "days":
                        if starttime == 0:
                            starttime = log[i][j]['time:timestamp']
                            base_year = starttime.year
                            log[i][j]['time:timestamp'] = datetime.datetime(year=base_year, month=1, day=1,
                                                                            hour=0,minute=0,second=0)
                        else:
                            startstr = starttime.strftime("%Y-%m-%d %H:%M:%S")
                            endstr = log[i][j]['time:timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                            start = datetime.datetime.strptime(startstr, '%Y-%m-%d %H:%M:%S')
                            ends = datetime.datetime.strptime(endstr, '%Y-%m-%d %H:%M:%S')
                            diff = relativedelta(ends, start)
                            years = diff.years
                            month = diff.months
                            days = diff.days
                            hours = diff.hours
                            minutes = diff.minutes
                            sectim = diff.seconds
                            try:
                                log[i][j]['time:timestamp'] = datetime.datetime(year=base_year + years, month=1 + month,
                                                                            day= 1+ days, hour=0,minute=0,second=0)
                                if time_exception_happend != 0:
                                    days += time_exception_happend.day
                                    log[i][j]['time:timestamp'] = datetime.datetime(year=base_year + years,
                                                                                    month=1 + month,
                                                                                    day=1 + days, hour=0,
                                                                                    minute=0, second=0)
                                    if log[i][j]['time:timestamp'] < time_exception_happend:
                                        log[i][j]['time:timestamp'] = time_exception_happend

                            except:
                                daysOfmonth = monthrange(log[i][j]['time:timestamp'].year, 1 + month)[1]
                                if days + 1 > daysOfmonth:
                                    month += 1
                                    days = days - daysOfmonth + 1
                                log[i][j]['time:timestamp'] = datetime.datetime(year=base_year + years,
                                                                                month=1 + month,
                                                                                day= days, hour=0, minute=0,
                                                                                second=0)
                    elif spectime == "original":
                        pass
                    k += 1
                    j += 1
                else:
                    del_list.append(log[i][j])
                    # log[i]._list.remove(log[i][j])
                    d += 1
                    j += 1
                    k += 1
            for x in del_list:
                log[i]._list.remove(x)
                # d += 1
                # x += 1
            if len(log[i]) == 0:
                deleteLog.append(i)
            #     else:
            #         log[i]._list.remove(log[i][j])
            #         d += 1
            # if j < len(log[i]):
            #     for k in range(len(log[i])-1, j - 1 ,-1):
            #         log[i]._list.remove(log[i][k])
            #         d += 1
            #         j += 1
            # if len(log[i]) == 0:
            #     deleteLog.append(i)
        for i in sorted(deleteLog, reverse=True):
            log._list.remove(log[i])
            d_l += 1
        log2 = EventLog([trace for trace in log], classifiers = self.log.classifiers)
        return log2, d, d_l

    #not used...............
    def suppression2(self, sup, simplifiedlog, spectime):
        deleteLog = []
        log_del = self.log
        log = self.log
        d = 0
        d_l = 0
        sup = [el[0] for el in sup]
        for i in range(0, len(log)):
            caseId = log[i].attributes["concept:name"]
            if caseId not in simplifiedlog.keys():
                deleteLog.append(i)
                continue
            j = 0
            del_list =[]
            while j < len(log[i]):
                if simplifiedlog[caseId]['trace'][j][0] not in sup:
                    if spectime == "seconds":
                        if j == 0:
                            starttime = log[i][j]['time:timestamp']
                            log[i][j]['time:timestamp'] = datetime.datetime(year=datetime.MINYEAR + 1970, month=1, day=1,
                                                                            hour=0, minute=0, second=0)
                        else:
                            timedif = log[i][j]['time:timestamp'] - starttime
                            years = int(timedif.days / 365)
                            daystime = timedif.days - years * 365
                            month, days = self.month_translate(daystime)
                            sectim = timedif.seconds
                            # 60sec -> 1 min, 60*60sec -> 60 min -> 1 hour
                            hours = int(sectim / 3600)
                            sectim = sectim - hours * 3600
                            minutes = int(sectim / 60)
                            sectim = sectim - minutes * 60
                            try:
                                log[i][j]['time:timestamp'] = datetime.datetime(year=datetime.MINYEAR + 1970, month=1 + month,
                                                                            day=1+days, hour=hours,
                                                                            minute=minutes, second=sectim)
                            except:
                                days = days -1
                                log[i][j]['time:timestamp'] = datetime.datetime(year=datetime.MINYEAR + 1970,
                                                                                month=1 + month,
                                                                                day=1 + days, hour=hours,
                                                                                minute=minutes, second=sectim)
                    elif spectime == "minutes":
                        if j == 0:
                            starttime = log[i][j]['time:timestamp']
                            log[i][j]['time:timestamp'] = datetime.datetime(year=datetime.MINYEAR + 1970, month=1, day=1,
                                                                            hour=0, minute=0,second=0)
                        else:
                            timedif = log[i][j]['time:timestamp'] - starttime
                            years = int(timedif.days / 365)
                            daystime = timedif.days - years * 365
                            month, days = self.month_translate(daystime)
                            sectim = timedif.seconds
                            # 60sec -> 1 min, 60*60sec -> 60 min -> 1 hour
                            hours = int(sectim / 3600)
                            sectim = sectim - hours * 3600
                            minutes = int(sectim / 60)
                            try:
                                log[i][j]['time:timestamp'] = datetime.datetime(year=datetime.MINYEAR + 1970, month=1 + month,
                                                                            day=1 + days, hour=hours,
                                                                            minute=minutes,second=0)
                            except:
                                days = days - 1
                                log[i][j]['time:timestamp'] = datetime.datetime(year=datetime.MINYEAR + 1970,
                                                                                month=1 + month,
                                                                                day=1 + days, hour=hours,
                                                                                minute=minutes, second=0)

                    elif spectime == "hours":
                        if j == 0:
                            starttime = log[i][j]['time:timestamp']
                            log[i][j]['time:timestamp'] = datetime.datetime(year=datetime.MINYEAR + 1970, month=1, day=1,
                                                                            hour=0,minute=0,second=0)
                        else:
                            timedif = log[i][j]['time:timestamp'] - starttime
                            years = int(timedif.days / 365)
                            daystime = timedif.days - years * 365
                            month, days = self.month_translate(daystime)
                            sectim = timedif.seconds
                            # 60sec -> 1 min, 60*60sec -> 60 min -> 1 hour
                            hours = int(sectim / 3600)
                            try:
                                log[i][j]['time:timestamp'] = datetime.datetime(year=datetime.MINYEAR + 1970, month=1 + month,
                                                                            day=1 + days, hour=hours,minute=0,second=0)
                            except:
                                days = days -1
                                log[i][j]['time:timestamp'] = datetime.datetime(year=datetime.MINYEAR + 1970,
                                                                                month=1 + month,
                                                                                day=1 + days, hour=hours, minute=0,
                                                                                second=0)

                    elif spectime == "days":
                        if j == 0:
                            starttime = log[i][j]['time:timestamp']
                            log[i][j]['time:timestamp'] = datetime.datetime(year=datetime.MINYEAR + 1970, month=1, day=1,
                                                                            hour=0,minute=0,second=0)
                        else:
                            timedif = log[i][j]['time:timestamp'] - starttime
                            years = int(timedif.days / 365)
                            daystime = timedif.days - years * 365
                            month, days = self.month_translate(daystime)
                            sectim = timedif.seconds
                            # 60sec -> 1 min, 60*60sec -> 60 min -> 1 hour
                            # days = int(sectim / 3600 * 24)
                            try:
                                log[i][j]['time:timestamp'] = datetime.datetime(year=datetime.MINYEAR + 1970, month=1 + month,
                                                                            day= 1+ days, hour=0,minute=0,second=0)
                            except:
                                days = days -1
                                log[i][j]['time:timestamp'] = datetime.datetime(year=datetime.MINYEAR + 1970,
                                                                                month=1 + month,
                                                                                day=1 + days, hour=0, minute=0,
                                                                                second=0)

                    j += 1
                else:
                    del_list.append(log[i][j])
                    # log[i]._list.remove(log[i][j])
                    d += 1
                    j += 1
            for x in del_list:
                log[i]._list.remove(x)
                # d += 1
                # x += 1
            if len(log[i]) == 0:
                deleteLog.append(i)
        for i in sorted(deleteLog, reverse=True):
            log._list.remove(log[i])
            d_l += 1
        log2 = EventLog([trace for trace in log])
        return log2, d, d_l

    def month_translate(self, daystime):
        if daystime <= 30:
            month = 0
            days = daystime
        elif daystime <= 58:
            month = 1
            days = daystime - 30
        elif daystime <= 89:
            month = 2
            days = daystime - 58
        elif daystime <= 119:
            month = 3
            days = daystime - 89
        elif daystime <= 150:
            month = 4
            days = daystime - 119
        elif daystime <= 180:
            month = 5
            days = daystime - 150
        elif daystime <= 211:
            month = 6
            days = daystime - 180
        elif daystime <= 242:
            month = 7
            days = daystime - 211
        elif daystime <= 273:
            month = 8
            days = daystime - 242
        elif daystime <= 303:
            month = 9
            days = daystime - 273
        elif daystime <= 334:
            month = 10
            days = daystime - 303
        elif daystime <= 365:
            month = 11
            days = daystime - 334
        if days != 0:
            days -= 1
        return month, days

    def get_relative_freq_in_log(self, list_traces): # get relative frequency of the events in the whole event log
        flat_list = [item for sublist in list_traces for item in sublist]
        flat_list_set = set(flat_list)
        flat_list_dict = {item: 0 for item in flat_list_set}
        tuple_list = map(tuple, flat_list)
        c = Counter(tuple_list)
        for items in c.items():
            freq = items[1] / len(flat_list)
            flat_list_dict[items[0]] = freq
        return flat_list_dict

    def get_relative_freq_in_variants(self, list_traces): #gets the relative frequency of events based on their appearnce in the variants

        list_tuple_traces = [tuple(x) for x in list_traces]
        tuple_traces = tuple(list_tuple_traces)
        c = Counter(tuple_traces) #variants with frequencies

        #events
        flat_list = [item for sublist in list_traces for item in sublist]
        flat_list_set = set(flat_list)
        flat_list_dict = {item: 0 for item in flat_list_set}

        for event in flat_list_set:
            for variant in c.items():
                if event in variant[0]:
                    flat_list_dict[event] += variant[1]/len(list_traces)

        return flat_list_dict

    def get_relative_freq(self,list_traces,utility_measure): #combines  get_relative_freq_in_log and get_relative_freq_in_variants
        freq_in_log = self.get_relative_freq_in_log(list_traces)
        freq_in_variant = self.get_relative_freq_in_variants(list_traces)
        final_freq = {}
        for event,freq in freq_in_log.items():
            final_freq[event] = (utility_measure[0] * freq_in_log[event]) + (utility_measure[1] * freq_in_variant[event])
        return final_freq