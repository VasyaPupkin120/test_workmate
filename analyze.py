import re
import sys
import time

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
FLAG_LINE = "django.request"

def parse_commandline():
    """
    Возвращает список позиционных параметров и словарь с ключевыми парамтерами и их значениями.
    Ключевые параметры без значения остаются None, то есть -l  преобразуется в  {"-l": None}.
    """
    all_args = sys.argv[1:]
    kwargs = {}
    args = []
    prev_is_kwargs = False
    key_kwargs = None
    
    for arg in all_args:
        if arg.startswith("-"):
            # обработка случая когда предыдыщуий параметр - ключевой параметр без значения вида -l
            if prev_is_kwargs:
                key_kwargs = arg
                kwargs[key_kwargs] = None
                continue
            key_kwargs = arg
            kwargs[key_kwargs] = None
            prev_is_kwargs = True
            continue
        if prev_is_kwargs:
            kwargs[key_kwargs] = arg
            prev_is_kwargs = False
            continue
        else:
            args.append(arg)
    return args, kwargs


def analyze_one_file(filename):
    """
    Создает и возвращает словарь с словарями. Ключи на верхнем уровне - названия ручек, 
    на нижнем урове - из списка типов событий. Подсчитывается количество событий:
       {"/api/v1/reviews/": {"DEBUG": 0, "INFO": 0, ...}} 

    """
    handlers_info = {}
    count_all_lines = 0
    count_django_request_lines = 0

    log_levels_group = "(" + "|".join(LOG_LEVELS) + ")"
    handler_name_group = r".*?(/\S+/)"
    pattern = re.compile(log_levels_group + handler_name_group)

    with open(filename, 'r') as f:
        for line in f:
            count_all_lines += 1
            if FLAG_LINE in line:
                count_django_request_lines += 1
                match = pattern.search(line) 
                if not match:
                    print(f"Строка '{line}' не соответствует шаблону")
                    continue
                if match.groups()[1] not in handlers_info.keys():
                    handlers_info[match.groups()[1]] = {}
                    for level in LOG_LEVELS:
                        handlers_info[match.groups()[1]][level] = 0
                handlers_info[match.groups()[1]][match.groups()[0]] += 1


    # подсчет количества всех логов по типам
    global_sum_LOG_LEVELS = {level: 0 for level in LOG_LEVELS}
    for handler in handlers_info:
        for level in global_sum_LOG_LEVELS:
            global_sum_LOG_LEVELS[level] += handlers_info[handler][level]

    # количество символов для выравнивания, максимум из длины заголовка и длины суммарного значения
    max_len_handlers = max([len(key) for key in handlers_info.keys()] + [len("HANDLER"),])
    len_levels = {level: 0 for level in LOG_LEVELS}
    for level, count in global_sum_LOG_LEVELS.items():
        len_levels[level] = max(len(str(count)), len(level))

    # вывод
    print(f"Total requests: {count_all_lines}", flush=True)
    print(f"Django requests: {count_django_request_lines}", flush=True)
    # заголовки таблицы
    space = 2
    print("HANDLER".ljust(max_len_handlers + space), end="")
    for level, len_level in len_levels.items():
        print(level.ljust(len_level + space), end="")
    print()
    # тело таблицы
    for handler, statistic in handlers_info.items():
        print(handler.ljust(max_len_handlers + space), end="")
        for level, count in statistic.items():
            print(str(count).ljust(len_levels[level] + space), end="")
        print()
    # итоги
    len_block = max_len_handlers + space
    for level, len_level in len_levels.items():
        len_block = len_block + len_level + space
    print("-" * len_block)

    print(" ".ljust(max_len_handlers + space), end="")
    for level, num_events in global_sum_LOG_LEVELS.items():
        print(str(num_events).ljust(len_levels[level] + space), end="")
    print()


    


def analyze(filenames, kwargs):
    analyze_one_file(filenames[0])




if __name__ == "__main__":
    start_time = time.time()
    filenames, kwargs = parse_commandline()
    analyze(filenames, kwargs)
    work_time = int(time.time() - start_time) 
    print(f"Время выполнениия: {work_time} сек.")

