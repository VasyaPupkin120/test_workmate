from analyze import *

def test_parse_commandline():
    assert parse_commandline(['app1.log', 'app2.log', '--report', 'test_handlers']) == (['app1.log', 'app2.log'], 
                                                                                        {'--report': 'test_handlers'})

def test_files_is_exists():
    assert files_is_exists(["app1.log", "asdf"]) == "asdf"
    assert files_is_exists(["app1.log", ]) == None

def test_analize_one_file():
    assert analyze_one_file("tests/test1.log") == {
            "/api/v1/reviews/": {"DEBUG": 1, "INFO":1, "WARNING": 1, "ERROR": 1, "CRITICAL": 1},
            "/api/v1/cart/": {"DEBUG": 1, "INFO":1, "WARNING": 1, "ERROR": 1, "CRITICAL": 1},
            }

def test_report_to_str_default():
    assert report_to_str_default(analyze_one_file("tests/test1.log")) == """\
---------------------------------------------------------
Total requests: 10
---------------------------------------------------------
HANDLER           DEBUG  INFO  WARNING  ERROR  CRITICAL  
---------------------------------------------------------
/api/v1/cart/     1      1     1        1      1         
/api/v1/reviews/  1      1     1        1      1         
---------------------------------------------------------
                  2      2     2        2      2         
---------------------------------------------------------
"""

def test_analyze():
    assert analyze(["tests/test1.log", "tests/test2.log"], {"--report": "handlers"}) == """\
---------------------------------------------------------
Total requests: 20
---------------------------------------------------------
HANDLER           DEBUG  INFO  WARNING  ERROR  CRITICAL  
---------------------------------------------------------
/api/v1/cart/     2      2     2        2      2         
/api/v1/reviews/  2      2     2        2      2         
---------------------------------------------------------
                  4      4     4        4      4         
---------------------------------------------------------
"""


def test_analyze_not_parameters():
    assert analyze([], {}) == "Отстутсвуют имена файлов."

def test_analyze_bad_filename():
    assert analyze(["this_file_not_extists_aqwerqwerpqiwuerp"], {}) == "Файл this_file_not_extists_aqwerqwerpqiwuerp не существует."



