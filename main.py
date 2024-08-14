from datetime import datetime
from collections import defaultdict
from statistics import mean
import time
 
 
class Log:
    def __init__(self, time_, type_, message_):
        self.time = time_
        self.type = type_
        self.message = message_
 
 
class LogAnalyzer:
    def __init__(self, log_lines_):
        self.log_lines = log_lines_
        self.logs = self.parse_log_lines()
 
    def parse_log_lines(self):
        logs = []
 
        for line in self.log_lines:
            log_entry = self.parse_log_entry(line)
            if log_entry:
                logs.append(log_entry)
 
        return logs
 
    @staticmethod
    def parse_log_entry(log_line):
        try:
            log_time_str, log_type, log_message = log_line.split(' - ', 2)
            log_time = datetime.strptime(log_time_str, "%H:%M:%S")
 
            return Log(time_=log_time, type_=log_type.translate(str.maketrans("", "", "[]")), message_=log_message)
 
        except ValueError:
            print("Malformed line: " + log_line)
            exit(1)
 
    def error_count_per_app(self):
        logs_per_type_per_app = defaultdict(lambda: defaultdict(int))
 
        for log in self.logs:
            app_type = log.message.split(' ')[0]
            logs_per_type_per_app[app_type][log.type] += 1
 
        for app_type in logs_per_type_per_app.keys():
            logs_per_type_per_app[app_type]["INFO"] = int(logs_per_type_per_app[app_type]["INFO"] / 2)
 
        return dict(logs_per_type_per_app)
 
    def avg_runtime(self):
        run_times = defaultdict(list)
        for log in self.logs:
            if log.type == "INFO" and "ran successfully" in log.message:
                app_type = log.message.split(" ")[0]
                run_time = log.message.split(" ")[-1]
                run_time = int(run_time[:-3])
                run_times[app_type].append(run_time)
        return {key: round(mean(value), 2) for (key, value) in run_times.items()}
 
    def failures_per_app(self):
        failures_per_app = defaultdict(int)
 
        for log in self.logs:
            if log.type == 'ERROR':
                app_type = log.message.split(' ')[0]
                failures_per_app[app_type] += 1
 
        return dict(failures_per_app)
 
    def app_with_most_errors(self):
        failed_runs_per_app = defaultdict(int)
        for log in self.logs:
            if log.type == "ERROR":
                app_type = log.message.split(' ')[0]
                failed_runs_per_app[app_type] = failed_runs_per_app[app_type] + 1
        if not failed_runs_per_app:
            return None, 0
        key = max(failed_runs_per_app, key=failed_runs_per_app.get)
        value = max(failed_runs_per_app.values())
        return key, value
 
    def app_with_most_successful_runs(self):
        successful_runs_per_app = defaultdict(int)
 
        for log in self.logs:
            if log.type == 'INFO' and 'ran successfully' in log.message:
                app_type = log.message.split(' ')[0]
                successful_runs_per_app[app_type] += 1
 
        if not successful_runs_per_app:
            return None, 0
 
        most_successful_app = max(successful_runs_per_app, key=successful_runs_per_app.get)
        return most_successful_app, successful_runs_per_app[most_successful_app]
 
    def most_failures_third(self):
        failures_per_third_of_day = defaultdict(int)
 
        for log in self.logs:
            hour = log.time.hour
            if log.type == 'ERROR':
                if 0 <= hour < 8:
                    failures_per_third_of_day['00:00:00 - 07:59:59'] += 1
                elif 8 <= hour < 16:
                    failures_per_third_of_day['08:00:00 - 15:59:59'] += 1
                else:
                    failures_per_third_of_day['16:00:00 - 23:59:59'] += 1
        if not failures_per_third_of_day:
            return None,0
 
        most_failures_third_of_day = max(failures_per_third_of_day, key=failures_per_third_of_day.get)
        return most_failures_third_of_day, failures_per_third_of_day[most_failures_third_of_day]
 
    def longest_shortest_runtimes(self):
        longest_runtime = -1
        longest_runtime_timestamp = None
        shortest_runtime = float('inf')
        shortest_runtime_timestamp = None
 
        for log in self.logs:
            if log.type == "INFO" and "ran successfully" in log.message:
                current_runtime = int(log.message.split()[-1][:-2])
 
                if current_runtime > longest_runtime:
                    longest_runtime = current_runtime
                    longest_runtime_timestamp = f'{log.time:%H:%M:%S}'
 
                if current_runtime < shortest_runtime:
                    shortest_runtime = current_runtime
                    shortest_runtime_timestamp = f'{log.time:%H:%M:%S}'
 
        return (longest_runtime, longest_runtime_timestamp), (shortest_runtime, shortest_runtime_timestamp)
 
    def most_active_hour_per_app(self):
        activities_per_hour = defaultdict(lambda: defaultdict(int))
 
        for log in self.logs:
            hour_range = f"{log.time.hour:02d}:00:00 - {log.time.hour:02d}:59:59"
            app_type = log.message.split(" ")[0]
            if app_type != "SYSTEM":
                activities_per_hour[hour_range][app_type] += 1
 
        if not activities_per_hour:
            return {None:None}
 
        max_activity = {}
 
        for app_type in {'FrontendApp', 'BackendApp', 'API'}:
            max_hour_range = max(activities_per_hour, key=lambda x: activities_per_hour[x][app_type])
            max_activity_count = activities_per_hour[max_hour_range][app_type]
            max_activity[app_type] = {max_hour_range: max_activity_count}
 
        return max_activity
 
    def failure_rate_per_app(self):
        failure_rate_per_app = {'FrontendApp': 0.0, 'BackendApp': 0.0, 'API': 0.0, 'SYSTEM': 0.0}
 
        total_logs_per_app = defaultdict(int)
        error_logs_per_app = defaultdict(int)
 
        for log in self.logs:
            app_type = log.message.split(' ')[0]
            total_logs_per_app[app_type] += 1
 
            if log.type == 'ERROR':
                error_logs_per_app[app_type] += 1
 
        for app_type in failure_rate_per_app:
            total_logs = total_logs_per_app[app_type]
            error_logs = error_logs_per_app[app_type]
 
            if total_logs > 0:
                failure_rate_per_app[app_type] = round((error_logs / total_logs) * 100, 2)
 
        return failure_rate_per_app
 
 
if __name__ == "__main__":
    with open("input.txt", "r") as input_file:
        log_lines = input_file.readlines()
    log_analyzer = LogAnalyzer(log_lines)
 
    print("Error count per app:")
    result_task_1 = log_analyzer.error_count_per_app()
    for app, log_counts in result_task_1.items():
        print(f'{app}: {dict(log_counts)}')
 
    print("\nAverage runtime:")
    result_task_2 = log_analyzer.avg_runtime()
    for app, avg_time in result_task_2.items():
        print(f'{app}: {avg_time:.2f} seconds')
 
    print("\nNo. of failures per app")
    result_task_3 = log_analyzer.failures_per_app()
    for app, failure_count in result_task_3.items():
        print(f'{app}: {failure_count}')
 
    print("\nApp with most errors:")
    result_task_4 = log_analyzer.app_with_most_errors()
    print(f'{result_task_4[0]}: {result_task_4[1]} errors')
 
    print("\nApp with most successful runs:")
    result_task_5 = log_analyzer.app_with_most_successful_runs()
    print(f'{result_task_5[0]}: {result_task_5[1]} successful runs')
 
    print("\nThird of day with most failures:")
    result_task_6 = log_analyzer.most_failures_third()
    print(f'{result_task_6[0]}: {result_task_6[1]} failures')
 
    print("\nLongest and shortest runtimes:")
    result_task_7 = log_analyzer.longest_shortest_runtimes()
    print(f"Longest runtime {result_task_7[0][0]}ms at {result_task_7[0][1]}")
    print(f"Shortest runtime {result_task_7[1][0]}ms at {result_task_7[1][1]}")
 
    print("\nMost active hour per app:")
    result_task_8 = log_analyzer.most_active_hour_per_app()
    for app, hour_range in result_task_8.items():
        print(f'{app}: {hour_range}')
 
    print("\nFailure rate per app:")
    result_task_9 = log_analyzer.failure_rate_per_app()
    for app, failure_rate in result_task_9.items():
        print(f'{app}: {failure_rate:.2f}%')
    
    #while True:
    print("workflow works 3.1")