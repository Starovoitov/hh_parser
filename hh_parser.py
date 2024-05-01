from dataclasses import fields
from datetime import datetime
import re
import csv
import time
import logging
import argparse

from bs4 import BeautifulSoup, SoupStrainer, Tag
from requests import Response
from retry import retry
import requests
import fake_user_agent

from data import (
    Currencies,
    EndOfCrawlError,
    Experience,
    Salary,
    SearchArea,
    UnknownError,
    default_headers,
    default_params,
    months_dict,
)

logger = logging.getLogger("root")


class HHParser:
    url = "https://hh.ru/search/vacancy"

    def __init__(
        self,
        search_params: dict = None,
        headers: dict = None,
        pause: float = 0.5,
        max_pages_number: int | None = 10,
        request_timeout: int = 30,
        dataset_loc: str = "file.csv",
        overwrite_csv: bool = False,
    ):
        if headers is None:
            headers = default_headers
        if search_params is None:
            search_params = default_params

        self.params = search_params
        self.headers = headers
        self.pause = pause
        self.current_page_number = 0
        self.max_pages_number = max_pages_number
        self.request_timeout = request_timeout
        self.dataset_loc = dataset_loc
        self._fieldnames = (
            [
                "title",
                "title_href",
                "company",
                "company_href",
                "location",
                "min_exp",
                "max_exp",
                "is_remote",
                "deployment",
            ]
            + [f.name for f in fields(Salary)]
            + ["published", "description"]
        )

        if overwrite_csv:
            with open(self.dataset_loc, "w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=self._fieldnames)
                writer.writeheader()

    def crawl_page(self, soup: BeautifulSoup) -> None:
        job_listings = soup.find_all("div", class_="serp-item serp-item_link")

        for job in job_listings:
            if isinstance(job, SoupStrainer):
                continue

            job_frame = {}

            try:
                title = job.find("h3", attrs={"data-qa": "bloko-header-3"}).findChild("a")
                title_href = title.attrs["href"]

                company = job.find("div", class_="vavacancy-creation-time-redesignedcancy-serp-item__meta-info-company")
                if company is None:
                    company = job.find("a", attrs={"data-qa": "vacancy-serp__vacancy-employer"}).parent
                company_href = company.find("a").attrs["href"] if company.find("a") else company.text
                location = job.find("div", attrs={"data-qa": "vacancy-serp__vacancy-address"})

                experience_element = job.find("div", attrs={"data-qa": "vacancy-serp__vacancy-work-experience"})
                experience = self.extract_experience_values(experience_element.text)

                is_remote_element = job.find("span", attrs={"data-qa": "vacancy-label-remote-work-schedule"})
                is_remote = bool(is_remote_element)

                salary_element = job.find("span", attrs={"data-qa": "vacancy-serp__vacancy-compensation"})
                salary = (
                    self.extract_salary_values(salary_string=salary_element.text)
                    if salary_element
                    else Salary(None, None, None, None)
                )

                deployment, description, published = self.crawl_full_description(title)

                job_frame["title"] = title.text.strip()
                job_frame["title_href"] = title_href
                job_frame["company"] = company.text.strip()
                job_frame["company_href"] = company_href
                job_frame["location"] = location.text.strip()

                experience_fields_dict = {field.name: getattr(experience, field.name) for field in fields(Experience)}
                job_frame.update(experience_fields_dict)

                job_frame["is_remote"] = is_remote
                job_frame["deployment"] = deployment.text.strip() if deployment else None
                job_frame["published"] = self.extract_date(published.text) if published else None
                job_frame["description"] = description.text.strip() if description else None

                salary_fields_dict = {field.name: getattr(salary, field.name) for field in fields(Salary)}
                job_frame.update(salary_fields_dict)

                self.write_down_page(job_frame)
            except AttributeError:
                logger.exception(f"Unusual rendering on page {self.current_page_number}, {job.text}")
                continue
            except Exception as e:
                raise UnknownError from e

    def write_down_page(self, data_frame: dict) -> None:
        logger.debug({k: v for k, v in data_frame.items() if k != "description"})
        values = [data_frame.get(key) for key in self._fieldnames]

        with open(self.dataset_loc, "a") as f:
            writer = csv.writer(f)
            writer.writerow(values)

    @retry(UnknownError, tries=5, delay=10)
    def turn_page(self) -> Response:
        logger.debug(f"Current page: {self.current_page_number + 1}")
        self.params["page"] = self.current_page_number
        self.headers["User-Agent"] = fake_user_agent.user_agent()
        response = requests.get(self.url, params=self.params, headers=self.headers, timeout=self.request_timeout)
        time.sleep(self.pause)

        if response.status_code == 200:
            self.crawl_page(BeautifulSoup(response.text, "html.parser"))

        self.current_page_number += 1

        return response

    def crawl_site(self):
        while self.current_page_number < self.max_pages_number if self.max_pages_number is not None else True:
            response = self.turn_page()
            if response.status_code == 404:
                raise EndOfCrawlError
            if response.status_code != 200:
                raise UnknownError

    def crawl_full_description(self, title: Tag) -> tuple[Tag, Tag, Tag]:
        response = requests.get(
            title.attrs["href"], params=self.params, headers=self.headers, timeout=self.request_timeout
        )
        time.sleep(self.pause)
        soup = BeautifulSoup(response.text, "html.parser")

        deployment = soup.find("p", attrs={"data-qa": "vacancy-view-employment-mode"})
        description = soup.find("div", attrs={"data-qa": "vacancy-description"})
        creation_time_tag = soup.find("p", class_="vacancy-creation-time-redesigned")
        published = creation_time_tag.find("span") if creation_time_tag else None

        return deployment, description, published

    def do_parse(self, area_name: str = None) -> None:
        try:
            logger.info(f"Start crawling, area - {area_name}")
            self.crawl_site()
        except EndOfCrawlError:
            logger.info(f"No more page exist, total - {self.current_page_number - 1}")
        except UnknownError as e:
            logger.critical(f"Unknown error: {e}")
        finally:
            logger.info("The end of crawling")

    @staticmethod
    def extract_salary_values(salary_string) -> Salary:
        # Remove non-breaking spaces and special characters
        salary_string_cleaned = re.sub(r"[^\d\s-]|(?<=\d) \d$", "", salary_string).strip()

        # Split the range
        salary_range = salary_string_cleaned.replace("\u202f", "").split()

        # Extract the minimum salary
        min_salary = int(salary_range[0])

        # Check if it's a range or a single salary
        if len(salary_range) > 1:
            max_salary = int(salary_range[1])
        else:
            # If it's a single salary, assign the same value to both min and max
            max_salary = min_salary
            if "до" in salary_string:
                min_salary = None
            if "от" in salary_string:
                max_salary = None

        currency = Currencies.Rub
        if Currencies.Dollar in salary_string:
            currency = Currencies.Dollar
        elif Currencies.Tenge in salary_string:
            currency = Currencies.Tenge
        elif Currencies.Euro in salary_string:
            currency = Currencies.Euro

        brutto = "на руки" not in salary_string

        return Salary(min_salary=min_salary, max_salary=max_salary, currency=currency, brutto=brutto)

    @staticmethod
    def extract_experience_values(experience_string) -> Experience:
        if experience_string == "Без опыта":
            return Experience(0, 0)
        # extract range of numbers
        experience_string_cleaned = re.sub(r"[^\d\s-]|(?<=\d) \d$", "", experience_string).strip()

        # Split the range
        experience_range = experience_string_cleaned.split()

        if len(experience_range) > 1:
            min_exp = int(experience_range[0])
            max_exp = int(experience_range[1])
        elif "от" in experience_string or "более" in experience_string or "не менее" in experience_string:
            min_exp = int(experience_range[0])
            max_exp = None
        else:
            min_exp = None
            max_exp = int(experience_range[0])

        if "месяц" in experience_string:
            min_exp = min_exp / 12 if min_exp else None
            max_exp = max_exp / 12 if max_exp else None

        return Experience(min_exp, max_exp)

    @staticmethod
    def extract_date(date_string):
        words = date_string.split()
        day = words[0]
        month = words[1]
        year = words[2]
        return datetime(int(year), months_dict.get(month), int(day))


def main(args):
    search_area = SearchArea()

    for area in fields(SearchArea):
        search_params = args.search_params
        search_params["area"] = getattr(search_area, area.name)
        if search_params["area"] == 0:
            continue
        HHParser(
            search_params=search_params,
            headers=args.headers,
            max_pages_number=args.max_pages_number,
            pause=args.requests_pause,
            request_timeout=args.request_timeout,
            dataset_loc=args.dataset,
            overwrite_csv=args.overwrite_csv,
        ).do_parse(area_name=area.name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--search_params", default=default_params, help="HH params for job search listing in default params dict"
    )
    parser.add_argument("--headers", default=default_headers, help="http headers to be applied in requests")
    parser.add_argument("--logs", default="parsers.log", help="crawling logs")
    parser.add_argument(
        "--requests_pause", default=0.3, help="pause in seconds between http requests to avoid blocking from hh side"
    )
    parser.add_argument("--request_timeout", default=30, help="timeout of http request in seconds")
    parser.add_argument("--max_pages_number", default=200, help="max number of pages allowed to crawl if they exist")
    parser.add_argument("--dataset", default="dataset.csv", help="accumulated dataset path")
    parser.add_argument(
        "--overwrite_csv",
        default=False,
        help="if True a new csv is created over the old one. Otherwise new records are appended at the end",
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s",
                        filename="log.log", filemode='w')

    main(args)
