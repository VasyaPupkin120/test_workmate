import os
import time
import sys
import re

NAMES_EVENTS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
# признак лога django
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


def files_is_exists(filenames:list):
    for file in filenames:
        if not os.path.isfile(file):
            return file
    return None


def handlers_info_to_str(handlers_info:dict, statistic:dict):
    """
    Все данные в строку, далее либо на печать в консоль либо в файл.
    """

    ret_line = ""
    space = 2 # пробелы между столбцами
    symbol_h_line = "-"

    # сумма количества событий для всех ручек
    sum_by_events = {name_event: 0 for name_event in NAMES_EVENTS}
    for _, events in handlers_info.items():
        for name_event, value_event in events.items():
            sum_by_events[name_event] += value_event

    # макс.ширина столбца с ручками. Расчет на основе длин названий ручек и заголовка для них
    name_handler_column = "HANDLER"
    width_column_handlers = max([len(key) for key in handlers_info.keys()] + [len(name_handler_column),]) 
    # расчет ширины для столбцов с событиями. Это либо ширина заголовка, либо ширина суммы
    widths_column_events = {name_event: 0 for name_event in NAMES_EVENTS}
    for name_event, value_event in sum_by_events.items():
        # где больше символов, в заголовке или в сумме
        widths_column_events[name_event] = max(len(str(value_event)), len(name_event)) 

    # ширина для горизонтальной отделяющей линии
    width_h_line = width_column_handlers + space
    for _, width in widths_column_events.items():
        width_h_line = width_h_line + width + space

    # общая информация
    ret_line = symbol_h_line * width_h_line + "\n"
    ret_line = ret_line + f"Total requests: {statistic['count_all']}" + "\n"
    ret_line = ret_line + f"Django requests: {statistic['count_django']}" + "\n"
    ret_line = ret_line + symbol_h_line * width_h_line + "\n"

    # заголовки таблицы
    names_column = name_handler_column.ljust(width_column_handlers + space)
    for name_event, width  in widths_column_events.items():
        names_column = names_column + name_event.ljust(width + space)
    ret_line = ret_line + names_column + "\n"
    ret_line = ret_line + symbol_h_line * width_h_line + "\n"

    # тело таблицы
    for handler_name, handler_events in handlers_info.items():
        line_table = handler_name.ljust(width_column_handlers + space)
        for name_event, value_event in handler_events.items():
            line_table += str(value_event).ljust(widths_column_events[name_event] + space)
        line_table += "\n"
        ret_line += line_table
    ret_line = ret_line + symbol_h_line * width_h_line + "\n"

    # итоги
    line_results = " ".ljust(width_column_handlers + space)
    for name_event, value_event in sum_by_events.items():
        line_results += str(value_event).ljust(widths_column_events[name_event] + space)
    line_results += "\n"
    ret_line += line_results
    ret_line = ret_line + symbol_h_line * width_h_line + "\n"

    # время работы
    ret_line = ret_line + f"Время работы: {statistic['work_time']} с." + "\n"
    ret_line = ret_line + symbol_h_line * width_h_line + "\n"

    return ret_line



def analyze_one_file(filename):
    """
    Создает и возвращает словарь с словарями. Ключи на верхнем уровне - названия ручек, 
    на нижнем урове - из списка типов событий. Подсчитывается количество событий:
       {"/api/v1/reviews/": {"DEBUG": 0, "INFO": 0, ...}} 

    """
    start_time = time.time()
    handlers_info = {}
    count_all_lines = 0
    count_django_request_lines = 0

    log_levels_group = "(" + "|".join(NAMES_EVENTS) + ")"
    handler_name_group = r".*?(/\S+/)"
    pattern = re.compile(log_levels_group + handler_name_group)

    with open(filename, 'r') as f:
        for line in f:
            count_all_lines += 1
            if FLAG_LINE in line:
                count_django_request_lines += 1
                match = pattern.search(line) 
                if not match:
                    print(f"Строка '{line}' содержит признак лога Django '{FLAG_LINE}' но не соответствует шаблону (ошибка в имени события или имени handler'a).")
                    continue
                if match.groups()[1] not in handlers_info.keys():
                    handlers_info[match.groups()[1]] = {}
                    for level in NAMES_EVENTS:
                        handlers_info[match.groups()[1]][level] = 0
                handlers_info[match.groups()[1]][match.groups()[0]] += 1

    work_time = int(time.time() - start_time) 
    statistic = {
            "count_all": count_all_lines, 
            "count_django": count_django_request_lines, 
            "work_time": work_time
            } 

    return handlers_info, statistic


def analyze(filenames, kwargs):
    if not filenames:
        print(f"Отстутсвуют имена файлов.")
        quit()

    err_filename = files_is_exists(filenames)
    if err_filename:
        print(f"Файл {err_filename} не существует.")
        quit()

    if not kwargs.get('--report'):
        filename_report = "handlers"
    else:
        if kwargs['--report'] != "handlers":
            print(f"Ваше имя файла отчета '{kwargs['--report']}' не совпадает с именем по умолчанию 'handlers'.")
            castom_filename = input("Использовать ваше имя файла отчета? (y/n)")
            if castom_filename not in ("y", "Y", "д", "Д", "yes", "Yes", "да", "Да"):
                quit()
            filename_report = kwargs['--report']

    for filename in filenames:
        handlers_info, statistic = analyze_one_file(filename)
        result_str = handlers_info_to_str(handlers_info, statistic)
        print(result_str)






if __name__ == "__main__":
    filenames, kwargs = parse_commandline()
    analyze(filenames, kwargs)

