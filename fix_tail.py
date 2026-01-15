
import os

file_path = "check_violations.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Define the corrupted block start (approximate) and the end
# We know "if seller_element:" is the start of the misaligned block
# And "except Exception as e:" is the end.

# We will construct the CORRECT block
correct_block = """        # --------------------------------
        # HIGHLIGHT TARGET
        if seller_element:
            try:
                driver.execute_script("arguments[0].style.border='5px solid red'; arguments[0].style.backgroundColor='yellow';", seller_element)
                # Scroll into view if needed (center it)
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", seller_element)
                time.sleep(1) # Wait for scroll
            except: pass
        else:
            # If we couldn't find/highlight seller, try to ensure Price is visible at least
            driver.execute_script("window.scrollTo(0, 0);")


        # --------------------------------

        png_data = driver.get_screenshot_as_png()
        
        # Annotation using PIL
        image = Image.open(io.BytesIO(png_data))
        draw = ImageDraw.Draw(image)
        width, height = image.size
        
        # Draw red border
        draw.rectangle([(0,0), (width-1, height-1)], outline="red", width=10)
        
        # Draw text box
        # Updated text to include Real Seller from page
        text = f"НАРУШЕНИЕ!\\nSKU: {sku}\\nБаза: {violation['competitor']}\\nПо факту: {real_seller}\\nИх цена: {violation['comp_price']} ₽\\nНаша цена: {violation['our_price']} ₽"
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
            
        text_bbox = draw.textbbox((50, 50), text, font=font)
        # Add padding
        draw.rectangle([text_bbox[0]-10, text_bbox[1]-10, text_bbox[2]+10, text_bbox[3]+10], fill="red")
        draw.text((50, 50), text, fill="white", font=font)
        
        output = io.BytesIO()
        image.save(output, format='PNG')
        output.seek(0)
        
        # Truncate strings just in case
        safe_comp = (violation['competitor'] or "")[:50]
        safe_real = (real_seller or "")[:50]
        
        # Send to TG
        from datetime import datetime
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        files = {'photo': ('violation.png', output, 'image/png')}
        caption = (f"🚨 **НАРУШЕНИЕ ЦЕНЫ!**\\n\\n"
                   f"🕒 Время: {now_str}\\n"
                   f"SKU: `{sku}`\\n"
                   f"🔗 [Товар на Ozon]({url})\\n\\n"
                   f"Магазин (База): *{safe_comp}*\\n"
                   f"Магазин (Факт): *{safe_real}*\\n"
                   f"Цена: **{violation['comp_price']} ₽**\\n"
                   f"(Наша: {violation['our_price']} ₽)")
                   
        data = {'chat_id': TG_CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}
        resp = requests.post(f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto", data=data, files=files)
        print(f"[VIOLATION_CHECK] Sent report status: {resp.status_code}")
        if resp.status_code != 200:
             print(f"[VIOLATION_CHECK] TG Error: {resp.text}")
        else:
             print(f"[VIOLATION_CHECK] Sent report for {sku}")
        
    except Exception as e:"""

# Locate the part of the file to replace
# We look for the marker lines
start_marker = "# HIGHLIGHT TARGET"
end_marker = "except Exception as e:"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    # We also need to include the line with 'except Exception as e:' in the replacement or handle it.
    # The replacement string ends with "except Exception as e:".
    # So we replace from start_marker (minus some whitespace maybe?) to end_idx + len(end_marker)
    
    # Actually, finding "if seller_element:" is safer as start.
    # But let's look at the file content again.
    # There is a line "# --------------------------------" before "# HIGHLIGHT TARGET"
    
    real_start = content.rfind("# --------------------------------", 0, start_idx)
    
    # Find the end of "except Exception as e:" line
    fin_end_idx = content.find(":", end_idx) + 1
    
    prefix = content[:real_start]
    suffix = content[fin_end_idx:]
    
    new_content = prefix + correct_block + suffix
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Fixed tail indentation.")
else:
    print("Could not find markers.")
