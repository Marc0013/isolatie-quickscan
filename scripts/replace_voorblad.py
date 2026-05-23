import re

with open('C:/Users/info/OneDrive/Documents/Ontwikkeling website/Tools en templates/isolatie-quickscan/scripts/generate_quickscan.js', encoding='utf-8') as f:
    content = f.read()

# Vind start en einde van maakVoorblad
start_marker = '// \u2500\u2500 SECTIE 1: Voorblad'
end_marker = '\nfunction maakInterpretatie'

start_idx = content.index(start_marker)
end_idx   = content.index(end_marker)

new_fn = open('C:/Users/info/OneDrive/Documents/Ontwikkeling website/Tools en templates/isolatie-quickscan/scripts/voorblad_nieuw.js', encoding='utf-8').read()

result = content[:start_idx] + new_fn + '\n' + content[end_idx+1:]

with open('C:/Users/info/OneDrive/Documents/Ontwikkeling website/Tools en templates/isolatie-quickscan/scripts/generate_quickscan.js', 'w', encoding='utf-8') as f:
    f.write(result)
print('Klaar')
