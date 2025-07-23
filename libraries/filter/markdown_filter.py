# libraries/filter/markdown_filter.py

from django import template
from django.template.defaultfilters import stringfilter
import markdown as md

register = template.Library()

@register.filter(name='markdown')  # 模板中仍然可以用 {{ 變數|markdown }}
@stringfilter
def render_markdown(value):
    return md.markdown(value, extensions=['markdown.extensions.fenced_code'])