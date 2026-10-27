import inspect
import re
from pathlib import Path

from doc.examples import test_client_applications


def test_readme_example():
    readme = (Path(__file__).parents[2] / "README.md").read_text()
    code = re.search(r"```python\n(.*?)```", readme, re.DOTALL).group(1)
    assert code == inspect.getsource(test_client_applications.test_login_shortcuts)
