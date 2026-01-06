from flask import current_app


def register_template_filters(app):
    @app.template_filter("system_name")
    def system_name(dummy):
        try:
            from src.services.config import Config

            return Config().get_system_name()
        except Exception as e:
            app.logger.error(f"Error in system_name filter: {e}")
            return "Internal System"

    @app.template_filter("maintenance_url")
    def maintenance_url(task_name):
        try:
            from src.services.config import Config
            from urllib.parse import quote

            config = Config()
            base_url = config._config["internal_system"]["base_url"]
            endpoint = config._config["internal_system"]["endpoints"][
                "maintenance_grid"
            ]

            params = [
                "status=NEW",
                "status=IN_PRG",
                "status=WT_PT",
                "status=SCH_HD",
                "status=RD_PICKUP",
                "status=RDY_TO_ASSG",
                "status=IN_PLAN",
                "status=IN_BUILD",
                "status=ASSGN",
                "assetViewIds=2642",
                f"name={quote(task_name)}",
            ]

            return f"{base_url}{endpoint}?{'&'.join(params)}"
        except Exception as e:
            app.logger.error(f"Error in maintenance_url filter: {e}")
            return "#"
