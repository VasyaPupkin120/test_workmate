import re

data = {}
log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
django_handler = "django.request"

count_lines = 0
with open("app1_large.log", 'r') as f:
    for line in f:
        count_lines += 1
        if not django_handler in line:
            continue
        for level in log_levels:
            if level in line:
                endpoint_key = re.search(r"/\S+/", line).group()
                if endpoint_key in data.keys():
                    data[endpoint_key][level] += 1
                else:
                    data[endpoint_key] = {}
                    for level in log_levels:
                        data[endpoint_key][level] = 0

# подсчет количества всех логов по типам
global_sum_log_levels = {level: 0 for level in log_levels}
for handler in data:
    for level in global_sum_log_levels:
        global_sum_log_levels[level] += data[handler][level]

# количество символов для выравнивания, максимум из длины заголовка и длины суммарного значения
max_len_handlers = max([len(key) for key in data.keys()] + [len("HANDLER"),])
len_levels = {level: 0 for level in log_levels}
for level, count in global_sum_log_levels.items():
    len_levels[level] = max(len(str(count)), len(level))




# вывод
print(f"Total requests: {count_lines}", flush=True)
# заголовки таблицы
space = 2
print("HANDLER".ljust(max_len_handlers + space), end="")
for level, len_level in len_levels.items():
    print(level.ljust(len_level + space), end="")
print()
# тело таблицы
for handler, statistic in data.items():
    print(handler.ljust(max_len_handlers + space), end="")
    for level, count in statistic.items():
        print(str(count).ljust(len_levels[level] + space), end="")
    print()
# итоги
print(" ".ljust(max_len_handlers + space), end="")
for level, num_events in global_sum_log_levels.items():
    print(str(num_events).ljust(len_levels[level] + space), end="")


    

# print(f"HANDLER {space * 3} {log_levels[0]} {space} {log_levels[1]} {space} {log_levels[2]} {space} {log_levels[3]} {space} {log_levels[4]}" )
# for handler in data:
#     print(handler, space, 
#           data[handler][log_levels[0]], 
#           )
#
#
# pprint.pprint(data)


                
