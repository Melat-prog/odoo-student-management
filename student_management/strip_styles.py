import re

with open('/home/melat/odoo18-dev/student_management/views/website_templates.xml', 'r') as f:
    content = f.read()

# Remove <t t-set="head_website"> ... </t>
content = re.sub(r'\s*<t t-set="head_website">.*?</t>', '', content, flags=re.DOTALL)

# Remove <t t-set="head"> ... </t>
content = re.sub(r'\s*<t t-set="head">.*?</t>', '', content, flags=re.DOTALL)

with open('/home/melat/odoo18-dev/student_management/views/website_templates.xml', 'w') as f:
    f.write(content)
