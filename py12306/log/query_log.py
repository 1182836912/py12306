import datetime
import json
import sys
from os import path
from py12306.log.base import BaseLog
from py12306.helpers.func import *


@singleton
class QueryLog(BaseLog):
    # 这里如果不声明，会出现重复打印，目前不知道什么原因
    logs = []
    thread_logs = {}
    quick_log = []

    data = {
        'query_count': 1,
        'last_time': '',
    }
    data_path = config.QUERY_DATA_DIR + 'status.json'

    LOG_INIT_JOBS = ''

    MESSAGE_GIVE_UP_CHANCE_CAUSE_TICKET_NUM_LESS_THAN_SPECIFIED = '余票数小于乘车人数，放弃此次提交机会'
    MESSAGE_QUERY_LOG_OF_EVERY_TRAIN = '{}-{}'
    MESSAGE_QUERY_LOG_OF_TRAIN_INFO = '{} {}'
    MESSAGE_QUERY_START_BY_DATE = '出发日期 {}: {} - {}'

    def __init__(self):
        super().__init__()
        self.init_data()

    def init_data(self):
        # 获取上次记录
        if Const.IS_TEST: return
        if path.exists(self.data_path):
            with open(self.data_path, encoding='utf-8') as f:
                result = f.read()
                if result:
                    result = json.loads(result)
                    self.data = {**self.data, **result}
                    self.print_data_restored()

    @classmethod
    def print_init_jobs(cls, jobs):
        """
        输出初始化信息
        :return:
        """
        self = cls()
        self.add_log('# 发现 {} 个任务 #'.format(len(jobs)))
        index = 1
        for job in jobs:
            self.add_log('================== 任务 {} =================='.format(index))
            for station in job.stations:
                self.add_log('出发站：{}    到达站：{}'.format(station.get('left'), station.get('arrive')))

            self.add_log('乘车日期：{}'.format(job.left_dates))
            self.add_log('坐席：{}'.format('，'.join(job.allow_seats)))
            self.add_log('乘车人：{}'.format('，'.join(job.members)))
            self.add_log('筛选车次：{}'.format('，'.join(job.allow_train_numbers if job.allow_train_numbers else ['不筛选'])))
            # 乘车日期：['2019-01-24', '2019-01-25', '2019-01-26', '2019-01-27']
            self.add_log('')
            index += 1

        self.flush()
        return self

    @classmethod
    def print_ticket_num_less_than_specified(cls, rest_num, job):
        self = cls()
        self.add_quick_log(
            '余票数小于乘车人数，当前余票数: {rest_num}, 实际人数 {actual_num}, 删减人车人数到: {take_num}'.format(rest_num=rest_num,
                                                                                         actual_num=job.member_num,
                                                                                         take_num=job.member_num_take))
        self.flush()
        return self

    @classmethod
    def print_ticket_seat_available(cls, left_date, train_number, seat_type, rest_num):
        self = cls()
        self.add_quick_log(
            '[ 查询到座位可用 出发时间 {left_date} 车次 {train_number} 座位类型 {seat_type} 余票数量 {rest_num} ]'.format(
                left_date=left_date,
                train_number=train_number,
                seat_type=seat_type,
                rest_num=rest_num))
        self.flush()
        return self

    @classmethod
    def print_ticket_available(cls, left_date, train_number, rest_num):
        self = cls()
        self.add_quick_log('检查完成 开始提交订单 '.format())
        self.notification('查询到可用车票', '时间 {left_date} 车次 {train_number} 余票数量 {rest_num}'.format(left_date=left_date,
                                                                                               train_number=train_number,
                                                                                               rest_num=rest_num))
        self.flush()
        return self

    @classmethod
    def print_query_error(cls, reason, code=None):
        self = cls()
        self.add_quick_log('查询余票请求失败')
        if code:
            self.add_quick_log('状态码 {}   '.format(code))
        if reason:
            self.add_quick_log('错误原因 {}   '.format(reason))
        self.flush(sep='\t')
        return self

    @classmethod
    def print_job_start(cls):
        self = cls()
        self.add_log('=== 正在进行第 {query_count} 次查询 === {time}'.format(query_count=self.data.get('query_count'),
                                                                     time=datetime.datetime.now()))
        self.refresh_data()
        if is_main_thread():
            self.flush()
        return self

    @classmethod
    def add_stay_log(cls, second):
        self = cls()
        self.add_log('安全停留 {}'.format(second))
        return self

    def print_data_restored(self):
        self.add_quick_log('============================================================')
        self.add_quick_log('|=== 查询记录恢复成功 上次查询 {last_date} ===|'.format(last_date=self.data.get('last_time')))
        self.add_quick_log('============================================================')
        self.add_quick_log('')
        self.flush()
        return self

    def refresh_data(self):
        self.data['query_count'] += 1
        self.data['last_time'] = str(datetime.datetime.now())
        self.save_data()

    def save_data(self):
        with open(self.data_path, 'w') as file:
            file.write(json.dumps(self.data))
