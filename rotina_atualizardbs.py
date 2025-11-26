from kob_car_api.common import CommonOps

operator = CommonOps(db_path='data/kob_car.db')
operator.sync_ops_tables(n=2)