# -*- coding: utf-8 -*-
from typing import Dict, Optional, Literal
from .exceptions import InvalidCurrency, InvalidSource, InvalidYearException, NoDataFoundException
from datetime import datetime
import requests
import logging

class Nazk:
    BASE_URL = 'http://213.199.45.147:5000/usd'
    TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6ImpzODEyMiJ9.6wUmjIT4tj5OWAfICSP62bjnEWO1w5LjNKrQM3KTn6c"

    def __init__(self, date_format='%d/%m/%Y', source='SBS', currency: Literal["USD"]="USD"):
        self.date_format = date_format
        
        if currency != "USD":
            raise InvalidCurrency(f'The {currency} currency is invalid.')
        
        if source in ['SBS', 'SUNAT']:
            self.source = source
        else:
            raise InvalidSource(f'The {source} source is invalid.')
    
    def _valid_date(self, date: datetime):
        if date > datetime.now():
            raise InvalidYearException('Information available until today.')
        if date.year < 2000:
            raise InvalidYearException('Information available from the 2000 year.')
        return True

    def _get(self, path: str, params: dict):
        url = f"{self.BASE_URL}{path}"
        headers = {"Authorization": f"Bearer {self.TOKEN}"}
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 422:
            logging.warning(f"{response.url} - Invalid parameter")
            logging.warning(response.text)
        elif response.status_code == 403:
            logging.warning(f"{response.url} - IP blocked")
        elif response.status_code == 429:
            logging.warning(f"{response.url} - Many requests add delay")
        elif response.status_code == 401:
            logging.warning(f"{response.url} - Invalid token or limited")
        else:
            logging.warning(f"{response.url} - Server Error status_code={response.status_code}")
    
    def _get_by_range(self, init_date: datetime, end_date: datetime):
        exchange_rates: Dict[str, any] = {}
        current_date = init_date
        while current_date <= end_date:
            data = self._get("/exchange", {"month": current_date.month, "year": current_date.year})
            for d in data:
                date = datetime.strptime(d['date'], "%Y-%m-%d")
                if current_date <= date <= end_date:
                    exchange_rates[datetime.strftime(date, "%d/%m/%Y")] = {
                        "buy": d["exchange_rate_buy"],
                        "sell": d["exchange_rate_sell"],
                    }
            if current_date.month == 12:
                current_date = current_date.replace(day=1, month=1, year=current_date.year + 1)
            else:
                current_date = current_date.replace(day=1, month=current_date.month + 1)

        return exchange_rates
    
    def _get_data(self, date: datetime, to_date:Optional[datetime]):
        data_dict: Dict[str, Dict[str, float]] = {}
        
        self._valid_date(date)
        
        if to_date:
            self._valid_date(to_date)
            data_dict = self._get_by_range(date, to_date)
        else:
            date_formatted = datetime.strftime(date, "%Y-%m-%d")
            data_json = self._get("/exchange", {"date": date_formatted})
            if data_json is not None:
                data_dict[datetime.strftime(date, self.date_format)] = {
                    "buy": float(data_json["exchange_rate_buy"]),
                    "sell": float(data_json["exchange_rate_sell"]),
                }
        
        return data_dict or None
    
    def get_exchange_rate(self, date: str, to_date: Optional[str]=None):
        date_dt = datetime.strptime(date, self.date_format)
        to_date_dt = datetime.strptime(to_date, self.date_format) if to_date else None
        data = self._get_data(date_dt, to_date_dt)
        if data is None: raise NoDataFoundException('No data found.')
        return data if date and to_date else list(data.values())[0]
