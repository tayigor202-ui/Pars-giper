import re

def extract_wb_id_from_url(url_or_id):
    if not url_or_id:
        return None
    value = str(url_or_id).strip()
    if 'wildberries.ru' in value or 'wb.ru' in value:
        # Pытаемся найти числовой ID в URL (обычно /catalog/ID/detail.aspx)
        match = re.search(r'/catalog/(\d+)/', value)
        if match:
            return match.group(1)
        return None
    
    if value.replace('.', '').replace(',', '').isdigit():
        return value.replace('.0', '').replace(',', '')
    return None

urls = [
    "https://www.wildberries.ru/catalog/1140308781/detail.aspx",
    "https://www.wildberries.ru/catalog/504869177/detail.aspx?targetUrl=GP",
    "12345678",
    "123456.0"
]

for u in urls:
    print(f"URL: {u} -> ID: {extract_wb_id_from_url(u)}")
