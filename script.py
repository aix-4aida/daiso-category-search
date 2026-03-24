import sqlite3
import re

try:
    conn = sqlite3.connect('c:/Users/301/dev4/daiso-category-search/backend/database/products.db')
    cur = conn.cursor()
    cur.execute('SELECT title, price, category FROM products ORDER BY RANDOM() LIMIT 4')
    items = cur.fetchall()

    def format_price(p):
        return f'{p:,}'

    html_products = ''
    for title, price, category in items:
        short_title = title if len(title) <= 12 else title[:11] + '...'
        cat_short = category.split('>')[-1].strip() if '>' in category else category
        if len(cat_short) > 6: cat_short = cat_short[:5]+'..'
        
        html_products += f'''                                <div class="product-thumb">
                                        <div style="width:100%;height:100px;background:#f5f5f5;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:12px;color:#999;text-align:center;padding:4px;word-break:keep-all;">
                                            {short_title}</div>
                                        <div class="price-tag">
                                            <span class="category" style="font-size:10px;">{cat_short}</span>
                                            <span class="price" style="font-size:11px;">{format_price(price)}원</span>
                                        </div>
                                    </div>\n'''

    replacement = f'<div class="banner-products">\n{html_products}                            </div>'

    with open('c:/Users/301/dev4/daiso-category-search/frontend/location.html', 'r', encoding='utf-8') as f:
        text = f.read()

    start_marker = '<div class="banner-products">'
    end_marker = '</div>\n                        </div>\n                    </div>\n                    <!-- Slide 2 -->'

    if start_marker in text and end_marker in text:
        start_idx = text.find(start_marker)
        end_idx = text.find(end_marker, start_idx)
        
        # we want to replace from start_marker up to the end_marker (but keep end_marker)
        new_text = text[:start_idx] + replacement + '\n                        ' + text[end_idx:]
        
        with open('c:/Users/301/dev4/daiso-category-search/frontend/location.html', 'w', encoding='utf-8') as f:
            f.write(new_text)
        with open('c:/Users/301/dev4/daiso-category-search/done.txt', 'w', encoding='utf-8') as f:
            f.write('SUCCESS')
    else:
        with open('c:/Users/301/dev4/daiso-category-search/done.txt', 'w', encoding='utf-8') as f:
            f.write('FAIL MARKER NOT FOUND')
except Exception as e:
    with open('c:/Users/301/dev4/daiso-category-search/done.txt', 'w', encoding='utf-8') as f:
        f.write('ERROR: ' + str(e))
