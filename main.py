from src.reports import spending_by_category
from src.views import views_info
from src.services import get_analize_cashback
import pandas as pd


def main() -> None:
    # главная страница
    data_time = "2021-05-01 00:00:00"
    res_views = views_info(data_time)
    # print(res_views)

    # сервисы
    rez_services = get_analize_cashback("data/operations.xlsx", 2021, 5)
    # print(rez_services)



if __name__ == "__main__":
    main()
