#    ┌─────────────────────────────────────────────────────────┐
#    │                                                         │
#    │                    Markdown to HTML                     │
#    │                                                         │
#    │ I would gladly not write my own code for this, but the  │
#    │ standard python libraries don't seem to handled nested  │
#    │   lists at all, and they are quite important in this    │
#    │ application.  So, here it is.  I'm not going to be too  │
#    │  dense with the comments because it's just a hot mess.  │
#    │                                                         │
#    └─────────────────────────────────────────────────────────┘
import re


def convert_md_to_html(md: str) -> str:
    html = ''
    md += '\n\n<EndOfFile>\n'

    lines = md.split('\n')

    state = 'NONE'
    paragraph = ''
    ul_stack = []  # Stack to keep track of nested <ul>
    ul_types = []

    padding = ''
    for line in lines:
        # Look for **Bold** cin comments or *italics* and convert them to HTML markup
        line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
        line = re.sub(r'\*(.*?)\*', r'<em>\1</em>', line)

        # is this line a bullet point or a numerical list?
        bullet_match = re.match(r'^(\s*)(\*|-|\+)\1*', line)
        list_match = re.match(r'^(\s*)(\d*)\.\s',line)

        if state == 'PARA' and (bullet_match or list_match or line.startswith('#') or len(line) == 0 or line == '<EOF>' or line.startswith("==")):
            html += '<p>' + paragraph + '</p>\n'
            paragraph = ''
            state = 'NONE'

        # Horizontal rule.
        if line.startswith("=="):
            html += '<hr/>\n'
            continue

        # Handle Bullets and Numerical Lists (UL and OL in HTML speak)
        # The code to handle the nesting of them is tricky, and I'm not sure if I've got it perfect,
        # but it seems to work OK
        if bullet_match or list_match:
            if bullet_match:
                level = len(bullet_match.group(1))
                length = len(bullet_match.group(0))
                ul_type = 'UL'
            else:
                level = len(list_match.group(1))
                length = len(list_match.group(0))
                ul_type = 'OL'

            if state != ul_type:
                ul_stack.append(level)
                ul_types.append(ul_type)
                html += f'<{ul_type}>\n'
                state = ul_type
            elif level > ul_stack[-1]:
                ul_stack.append(level)
                ul_types.append(ul_type)
                html += f'<{ul_type}>\n'
            elif level < ul_stack[-1]:
                while len(ul_stack) > 0 and level < ul_stack[-1]:
                    ul_stack.pop()
                    html += f'</{ul_types[-1]}>\n'
                    ul_types.pop()
            html += '<li>' + line[length:] + '</li>\n'
            continue

        if state == 'UL' or state == 'OL':
            if len(line) == 0:
                padding = '<br/>\n'
                continue
            else:
                while ul_stack:
                    ul_stack.pop()
                    html += f'</{ul_types[-1]}>\n'
                    ul_types.pop()
                state = 'NONE'

        if len(padding) > 0:
            html += padding
            padding = ''
        if line == '<EndOfFile>':
            break

        found = False
        for i in range(6, 0, -1):
            if line.startswith('#' * i):
                html += f'<h{i}>{line[i:].strip()}</h{i}\n'
                found = True
                break
        if found:
            continue

        paragraph += line + '\n'
        state = 'PARA'

    return html