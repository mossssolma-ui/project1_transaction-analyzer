import pandas as pd

from src.reports import spending_by_category
from src.services import get_analize_cashback
from src.views import views_info


def main() -> None:
    # главная страница
    data_time = "2021-05-01 00:00:00"
    res_views = views_info(data_time)
    print(res_views)

    # сервисы
    rez_services = get_analize_cashback("data/operations.xlsx", 2021, 5)
    print(rez_services)

    # отчеты
    df_for_reports = pd.read_excel("data/operations.xlsx")
    df_for_reports["Дата операции"] = pd.to_datetime(df_for_reports["Дата операции"], dayfirst=True)

    category_report = spending_by_category(df_for_reports, "Супермаркеты", "2021-05-31")
    print(f"Траты по категории 'Супермаркеты': {len(category_report)} записей")


if __name__ == "__main__":
    main()
