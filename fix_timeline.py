import re

with open('templates/unit_history.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Replace the Content box layout
old_content_pattern = r'<!-- Content -->.*?</div>\s*</div>\s*{% empty %}'
new_content = '''<!-- Content -->
            <div class="pt-1.5 pb-2">
                <div class="flex flex-col md:flex-row md:items-center justify-between mb-2">
                    <h4 class="font-bold text-gray-900 text-base flex items-center space-x-2">
                        <span>{{ log.get_action_display }}</span>
                    </h4>
                    <span class="text-xs font-bold text-gray-400 mt-1 md:mt-0">{{ log.timestamp|date:"d M Y, H:i" }}</span>
                </div>
                
                {% if log.employee %}
                <div class="flex items-center space-x-2 mb-2">
                    <div class="w-6 h-6 rounded-full bg-kerinci-light text-kerinci flex items-center justify-center font-bold text-[9px] uppercase">{{ log.employee.name|make_list|first }}</div>
                    <div>
                        <p class="font-bold text-gray-700 text-xs">{{ log.employee.name }}</p>
                    </div>
                </div>
                {% endif %}

                {% if log.notes %}
                <p class="text-sm text-gray-600 mt-1.5 leading-relaxed">{{ log.notes }}</p>
                {% endif %}
            </div>
        </div>
        {% empty %}'''

c = re.sub(old_content_pattern, new_content, c, flags=re.DOTALL)

# Adjust the spacing between timeline items (it used to be space-y-10, change to space-y-8 to fit the sleeker design)
c = c.replace('space-y-10', 'space-y-8')

# Remove the quotes around log.notes if the user didn't like them, I'll remove the quotes from the template.

with open('templates/unit_history.html', 'w', encoding='utf-8') as f:
    f.write(c)
