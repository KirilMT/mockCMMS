import json
import os
from pathlib import Path


class ConfigValidationError(Exception):
    pass


class Config:
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._load_config()

    def _load_config(self):
        config_path = Path(__file__).parent.parent.parent / "config" / "config.json"
        try:
            with open(config_path, "r") as f:
                self._config = json.load(f)
        except FileNotFoundError:
            # Fallback to example config
            example_path = config_path.parent / "config.example.json"
            with open(example_path, "r") as f:
                self._config = json.load(f)

        self._validate_config()

    def get_ticket_url(self, ticket_id):
        base_url = self._config["internal_system"]["base_url"]
        endpoint = self._config["internal_system"]["endpoints"]["ticket_view"]
        return base_url + endpoint.format(ticket_id=ticket_id)

    def get_maintenance_grid_url(self, **params):
        base_url = self._config["internal_system"]["base_url"]
        endpoint = self._config["internal_system"]["endpoints"]["maintenance_grid"]
        url = base_url + endpoint
        if params:
            query_params = "&".join(f"{k}={v}" for k, v in params.items())
            url += f"?{query_params}"
        return url

    def get_system_name(self):
        return self._config["internal_system"]["name"]

    def _validate_config(self):
        required_fields = [
            ["internal_system", "name"],
            ["internal_system", "base_url"],
            ["internal_system", "endpoints", "ticket_view"],
            ["internal_system", "endpoints", "maintenance_grid"],
        ]

        for field_path in required_fields:
            current = self._config
            try:
                for field in field_path:
                    current = current[field]
                if not current:
                    raise ConfigValidationError(
                        f"Empty value for {'.'.join(field_path)}"
                    )
            except (KeyError, TypeError):
                raise ConfigValidationError(
                    f"Missing required field: {'.'.join(field_path)}"
                )

    @staticmethod
    def get_fixed_datetime():
        import os
        from datetime import datetime

        fixed_date = os.getenv("DEBUG_FIXED_DATE")
        if fixed_date:
            try:
                return datetime.fromisoformat(fixed_date.replace("Z", "+00:00"))
            except:
                pass
        return None
