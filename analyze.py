import os
import sys
import re
import time
from multiprocessing import Pool

NAMES_EVENTS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
# признак лога django
FLAG_LINE = "django.request"

def parse_commandline(test_args=None):
    """
    Возвращает список позиционных параметров и словарь с ключевыми парамтерами и их значениями.
    Ключевые параметры без значения остаются None, то есть -l  преобразуется в  {"-l": None}.
    Параметр all_args нужен для тестирования.
    """
    if test_args:
        all_args = test_args
    else:
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


def report_to_str_default(report:dict):
    """
    Вариант отчета по умолчанию.
    Все данные в строку, далее либо на печать в консоль либо в файл.
    """

    ret_line = ""
    space = 2 # пробелы между столбцами
    symbol_h_line = "-"

    report = dict(sorted(report.items()))
    # сумма количества событий для всех ручек
    sum_by_events = {name_event: 0 for name_event in NAMES_EVENTS}
    for _, events in report.items():
        for name_event, value_event in events.items():
            sum_by_events[name_event] += value_event

    # макс.ширина столбца с ручками. Расчет на основе длин названий ручек и заголовка для них
    name_handler_column = "HANDLER"
    width_column_handlers = max([len(key) for key in report.keys()] + [len(name_handler_column),]) 
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
    total_requests = 0
    for _, value_event in sum_by_events.items():
        total_requests += value_event
    ret_line = ret_line + f"Total requests: {total_requests}" + "\n"
    ret_line = ret_line + symbol_h_line * width_h_line + "\n"

    # заголовки таблицы
    names_column = name_handler_column.ljust(width_column_handlers + space)
    for name_event, width  in widths_column_events.items():
        names_column = names_column + name_event.ljust(width + space)
    ret_line = ret_line + names_column + "\n"
    ret_line = ret_line + symbol_h_line * width_h_line + "\n"

    # тело таблицы
    for handler_name, handler_events in report.items():
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

    return ret_line



def analyze_one_file(filename):
    """
    Создает и возвращает словарь с словарями. Ключи на верхнем уровне - названия ручек, 
    на нижнем урове - из списка типов событий. Подсчитывается количество событий:
       {"/api/v1/reviews/": {"DEBUG": 0, "INFO": 0, ...}} 

    """
    report = {}

    log_levels_group = "(" + "|".join(NAMES_EVENTS) + ")"
    handler_name_group = r".*?(/\S+/)"
    pattern = re.compile(log_levels_group + handler_name_group)

    with open(filename, 'r') as f:
        for line in f:
            if FLAG_LINE in line:
                match = pattern.search(line) 
                if not match:
                    print(f"Строка '{line}' содержит признак лога Django '{FLAG_LINE}' но не соответствует шаблону (ошибка в имени события или имени handler'a).")
                    continue
                if match.groups()[1] not in report.keys():
                    report[match.groups()[1]] = {event_name: 0 for event_name in NAMES_EVENTS}
                report[match.groups()[1]][match.groups()[0]] += 1
    return report


def summarize(reports:list)->dict:
    # сумма количества событий для всех ручек
    summarize_report = {}
    for report in reports:
        for handler_name, handler_events in report.items():
            if handler_name not in summarize_report.keys():
                summarize_report[handler_name] = {event: 0 for event in NAMES_EVENTS}
            for name_event, value_event in handler_events.items():
                summarize_report[handler_name][name_event] += value_event
    return summarize_report


def analyze(filenames:list, kwargs:dict):
    if not filenames:
        return "Отстутсвуют имена файлов."

    err_filename = files_is_exists(filenames)
    if err_filename:
        return f"Файл {err_filename} не существует."
        

    if not kwargs.get('--report'):
        filename_report = "handlers"
    else:
        if kwargs['--report'] != "handlers":
            print(f"Ваше имя файла отчета \'{kwargs['--report']}\' не совпадает с именем по умолчанию 'handlers'.")
            castom_filename = input("Использовать ваше имя файла отчета? (y/n)")
            if castom_filename not in ("y", "Y", "д", "Д", "yes", "Yes", "да", "Да"):
                return "Отказ от нестандартного имени отчета. Остановка работы."
        filename_report = kwargs['--report']

    reports = Pool().map(analyze_one_file, filenames)

    summarize_report = summarize(reports)
    resultat = report_to_str_default(summarize_report)
    with open(filename_report, "w") as f:
        f.write(resultat)
    return resultat



if __name__ == "__main__":
    start_time = time.time()
    filenames, kwargs = parse_commandline()
    print(analyze(filenames, kwargs))
    print("Время работы: ", int(time.time() - start_time), " секунд")



