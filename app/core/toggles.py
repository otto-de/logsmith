from app.core import files


class Toggles:
    def __init__(self):
        self.run_script: bool = None

    def initialize(self) -> None:
        toggles = files.load_toggles()
        self.run_script = toggles.get('run_script', True)

    def toggle_run_script(self) -> None:
        self.run_script = not self.run_script
        self.save_toggles()

    def save_toggles(self) -> None:
        files.save_toggles_file({
            'run_script': self.run_script,
        })
