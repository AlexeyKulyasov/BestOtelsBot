import unittest

from executor_commands import CmdSortByPriceAndDist


def extract_result(hotels: list) -> list:
    """ Приведение полученного результата к формату подходящему
        для сравнения с ожидаемым результатом.
    """
    res = [{'price_exact': hotel['price_exact'],
            'to_center_exact': hotel['to_center_exact']
            } for hotel in hotels]
    return res


class TestCmdBestDeal(unittest.TestCase):
    """ Класс для тестирования команды "bestdeal" на корректность обработки результатов api запросов
        при указании различных диапазонов дистанций отелей от центра города. Для тестирования используются
        три json файла (папка debug_data) с сохраненными результатами api запросов (Часть полученной
         информации была отредактирована). Нумерация файлов соответстует номеру страницы с api запросом.
    """

    def setUp(self):
        api_params = {'sortOrder': 'DISTANCE_FROM_LANDMARK'}
        cmd_options = {'size_result': 0}
        self.implementer = CmdSortByPriceAndDist(api_params, cmd_options, True)

    def test_out_left_range(self):
        """ Выход за левый диапазон. Ожидаемый результат: вывод первых n отелей. """

        self.implementer.cmd_options['range_dist'] = (0.2, 0.5)
        self.implementer.required_size_result = 3
        result_expected = [{'price_exact': 3402.0, 'to_center_exact': 0.8},
                           {'price_exact': 8592.72, 'to_center_exact': 0.9},
                           {'price_exact': 8640.0, 'to_center_exact': 0.7}]
        result = self.implementer.start()
        received_result = extract_result(result.hotels)
        self.assertEqual(result_expected, received_result, 'Not matched')

    def test_out_right_range(self):
        """ Выход за правый диапазон. Ожидаемый результат: вывод последних n отелей. """

        self.implementer.cmd_options['range_dist'] = (2.8, 3)
        self.implementer.required_size_result = 3
        result_expected = [{'price_exact': 3581.51, 'to_center_exact': 2.5},
                           {'price_exact': 6412.5, 'to_center_exact': 2.7},
                           {'price_exact': 8250.0, 'to_center_exact': 2.6}]
        result = self.implementer.start()
        received_result = extract_result(result.hotels)
        self.assertEqual(result_expected, received_result, 'Not matched')

    def test_true_size_result_on_1st_page(self):
        """ Попадание в диапазон с соответствующим размером вывода (в рамках 1-й страницы) """

        self.implementer.cmd_options['range_dist'] = (1, 1.3)
        self.implementer.required_size_result = 3
        result_expected = [{'price_exact': 3000.0, 'to_center_exact': 1.1},
                           {'price_exact': 3402.0, 'to_center_exact': 1.0},
                           {'price_exact': 3402.0, 'to_center_exact': 1.2}]
        result = self.implementer.start()
        received_result = extract_result(result.hotels)
        self.assertEqual(result_expected, received_result, 'Not matched')

    def test_true_size_result_on_third_page(self):
        """ Попадание в диапазон с соответствующим размером вывода (в рамках 3-й страницы) """

        self.implementer.cmd_options['range_dist'] = (2, 2.5)
        self.implementer.required_size_result = 4
        result_expected = [{'price_exact': 3570.0, 'to_center_exact': 2.5},
                           {'price_exact': 3581.51, 'to_center_exact': 2.5},
                           {'price_exact': 3762.0, 'to_center_exact': 2.0},
                           {'price_exact': 4050.0, 'to_center_exact': 2.2}]
        result = self.implementer.start()
        received_result = extract_result(result.hotels)
        self.assertEqual(result_expected, received_result, 'Not matched')

    def test_true_size_result_in_end_1st_and_start_second_page(self):
        """ Попадание в диапазон с соответствующим размером вывода (в рамках конца 1-й и начало 2-й страницы) """

        self.implementer.cmd_options['range_dist'] = (1.3, 1.8)
        self.implementer.required_size_result = 4
        result_expected = [{'price_exact': 3676.5, 'to_center_exact': 1.8},
                           {'price_exact': 7560.0, 'to_center_exact': 1.5},
                           {'price_exact': 7943.25, 'to_center_exact': 1.3},
                           {'price_exact': 8570.0, 'to_center_exact': 1.5}]
        result = self.implementer.start()
        received_result = extract_result(result.hotels)
        self.assertEqual(result_expected, received_result, 'Not matched')

    def test_true_size_result_on_all_three_pages(self):
        """ Попадание в диапазон с соответствующим размером вывода (в рамках всех трёх страниц) """

        self.implementer.cmd_options['range_dist'] = (1.2, 2.5)
        self.implementer.required_size_result = 4
        result_expected = [{'price_exact': 3402.0, 'to_center_exact': 1.2},
                           {'price_exact': 3570.0, 'to_center_exact': 2.5},
                           {'price_exact': 3581.51, 'to_center_exact': 2.5},
                           {'price_exact': 3676.5, 'to_center_exact': 1.8}]
        result = self.implementer.start()
        received_result = extract_result(result.hotels)
        self.assertEqual(result_expected, received_result, 'Not matched')

    def test_true_size_result_on_last_page_with_out_range(self):
        """ Попадание в диапазон с соответствующим размером вывода (в рамках последней страницы,
            с правой стороной диапазона выходящего за пределы максимальной дистанции отеля)
        """

        self.implementer.cmd_options['range_dist'] = (2.5, 3.0)
        self.implementer.required_size_result = 4
        result_expected = [{'price_exact': 3570.0, 'to_center_exact': 2.5},
                           {'price_exact': 3581.51, 'to_center_exact': 2.5},
                           {'price_exact': 6412.5, 'to_center_exact': 2.7},
                           {'price_exact': 8250.0, 'to_center_exact': 2.6}]
        result = self.implementer.start()
        received_result = extract_result(result.hotels)
        self.assertEqual(result_expected, received_result, 'Not matched')

    def test_false_size_result_in_one_page(self):
        """ Попадание в диапазон с меньшим размером вывода (в рамках одной страницы) """

        self.implementer.cmd_options['range_dist'] = (0.3, 0.9)
        self.implementer.required_size_result = 4
        result_expected = [{'price_exact': 3402.0, 'to_center_exact': 0.8},
                           {'price_exact': 8592.72, 'to_center_exact': 0.9},
                           {'price_exact': 8640.0, 'to_center_exact': 0.7}]
        result = self.implementer.start()
        received_result = extract_result(result.hotels)
        self.assertEqual(result_expected, received_result, 'Not matched')

    def test_false_size_result_in_end_second_without_continuing_on_next_page(self):
        """ Попадание в диапазон с меньшим размером вывода (в рамках конца второй страницы
            с отсутствием продолжения диапазона на следующей)
        """
        self.implementer.cmd_options['range_dist'] = (1.8, 1.9)
        self.implementer.required_size_result = 5
        result_expected = [{'price_exact': 3676.5, 'to_center_exact': 1.8},
                           {'price_exact': 3897.0, 'to_center_exact': 1.9},
                           {'price_exact': 4470.0, 'to_center_exact': 1.9}]
        result = self.implementer.start()
        received_result = extract_result(result.hotels)
        self.assertEqual(result_expected, received_result, 'Not matched')
