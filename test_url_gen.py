from core.lemana_utils import get_lemana_regional_url

# Test cases
url1 = "https://lemanapro.ru/product/holodilnik-hyundai-cc20031h-444x1518-sm-cvet-belyy-92330488/"
url2 = "https://moscow.lemanapro.ru/product/item-123"
url3 = "https://lemanapro.ru/product/item-456?foo=bar"

region_klin = 8232 # klin
region_moscow = 34 # moscow

print(f"Original: {url1}")
print(f"Klin (8232): {get_lemana_regional_url(url1, region_klin)}")
print("-" * 20)

print(f"Original: {url2}")
print(f"Klin (8232): {get_lemana_regional_url(url2, region_klin)}")
print("-" * 20)

print(f"Original: {url3}")
print(f"Klin (8232): {get_lemana_regional_url(url3, region_klin)}")
