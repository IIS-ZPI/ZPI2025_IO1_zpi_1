import re
import requests

NBP_TABLE_URLS = [
        "https://api.nbp.pl/api/exchangerates/tables/A?format=json",
        "https://api.nbp.pl/api/exchangerates/tables/B?format=json"
    ]

def validate_currency(code: str) -> None:
    if not is_iso4217_format(code):
        raise ValueError (
            f"Invalid currency format: {code}. Must be ISO 4217 (3 uppercase letters, e.g. USD, EUR)."
        )

    valid_codes = fetch_all_nbp_codes()

    if code not in valid_codes:
        raise ValueError(
            f"Currency '{code}' is not supported by NBP."
        )

def is_iso4217_format(code: str) -> bool:
    ISO4217_REGEX = re.compile(r"^[A-Z]{3}$")
    return bool(ISO4217_REGEX.match(code))

def fetch_all_nbp_codes() -> set[str]:
    codes_a = fetch_nbp_codes(NBP_TABLE_URLS[0])
    codes_b = fetch_nbp_codes(NBP_TABLE_URLS[1])

    # PLN is not listed in A/B tables (NBP base currency)
    return codes_a.union(codes_b).union({"PLN"})

def fetch_nbp_codes(url: str) -> set[str]:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        rates = data[0]["rates"]
        return {rate["code"] for rate in rates}