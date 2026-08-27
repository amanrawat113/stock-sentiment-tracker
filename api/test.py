import requests

BSE_URL = "https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
    "Referer": "https://www.bseindia.com/",
    "sec-ch-ua": '"Not=A?Brand";v="99", "Google Chrome";v="151", "Chromium";v="151"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

params = {
    "pageno": 1,
    "strCat": -1,
    "strPrevDate": "20260828",
    "strScrip": "",
    "strSearch": "P",
    "strToDate": "20260828",
    "strType": "C",
    "subcategory": -1,
}

response = requests.get(BSE_URL, headers=HEADERS, params=params, timeout=15)
print("Status:", response.status_code)
print("Raw response:", response.text[:1000])