import re

with open("veridia-ajans.html", "r", encoding="utf-8") as f:
    html = f.read()

# Extract styles
style_match = re.search(r'<style>(.*?)</style>', html, re.DOTALL)
if style_match:
    with open("assets/shared.css", "w", encoding="utf-8") as f:
        f.write(style_match.group(1).strip())
    # Replace style with link
    html = html.replace(style_match.group(0), '<link rel="stylesheet" href="/assets/shared.css">')

# We can also extract the cursor and nav JS if we want, but let's just do CSS for now to make sure styles overlap exactly.
# Note: Actually it is tricky to separate JS without error handling. So we will write a tiny blog.js for the cursor.

with open("veridia-ajans.html", "w", encoding="utf-8") as f:
    f.write(html)

print("CSS extracted successfully")
