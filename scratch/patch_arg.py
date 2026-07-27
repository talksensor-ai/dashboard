with open('e:\\talk\\pipeline\\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("    parser.add_argument('--skip-time', type=int, default=0, help='Seconds to skip from start')", "parser.add_argument('--skip-time', type=int, default=0, help='Seconds to skip from start')")

with open('e:\\talk\\pipeline\\main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed indentation')
