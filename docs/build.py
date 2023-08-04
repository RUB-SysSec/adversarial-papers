from jinja2 import Template
import json
from pathlib import Path

config = json.loads(Path("config.json").read_text())
template = Path("index.template.html")


template = Template(template.read_text())
render_out = template.render(papers=config)
Path('index.html').write_text(render_out)