"""
Script to export OpenAPI schema from FastAPI application.

This script dynamically imports a FastAPI application and exports
the OpenAPI specification to a JSON file without starting the server.

Usage:
    python scripts.py module:app --output openapi.json
    python scripts.py module:create_app --factory --output openapi.json
"""

import argparse
import importlib
import json
import sys
from pathlib import Path


def import_app(app_string: str, is_factory: bool = False):
    """
    Import FastAPI application from a module string.

    Args:
        app_string: String in format "module.path:app_name" or "module.path:factory_function"
        is_factory: If True, the imported object is called as a factory function

    Returns:
        FastAPI application instance
    """
    if ":" not in app_string:
        raise ValueError(
            f"Invalid app string format: {app_string}. Expected format: 'module:attribute'"
        )

    module_path, app_name = app_string.split(":", 1)

    print(f"Importing {app_name} from {module_path}...")
    module = importlib.import_module(module_path)
    app_obj = getattr(module, app_name)

    if is_factory:
        print(f"Calling factory function {app_name}()...")
        return app_obj()
    else:
        return app_obj


def export_openapi_schema(
    app_string: str, output_path: str, is_factory: bool = False
) -> None:
    """
    Export OpenAPI schema from FastAPI app to a JSON file.

    Args:
        app_string: String in format "module:app" or "module:factory"
        output_path: Path where to save the OpenAPI schema JSON file
        is_factory: If True, treat the imported object as a factory function
    """
    app = import_app(app_string, is_factory)

    print("Generating OpenAPI schema...")
    openapi_schema = app.openapi()

    # Ensure the output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"Writing schema to {output_path}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)

    print(f"✓ OpenAPI schema successfully exported to {output_path}")
    print(f"  Title: {openapi_schema.get('info', {}).get('title', 'N/A')}")
    print(f"  Version: {openapi_schema.get('info', {}).get('version', 'N/A')}")
    print(f"  Endpoints: {len(openapi_schema.get('paths', {}))}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Export OpenAPI schema from FastAPI application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts.py main:app --output openapi.json
  python scripts.py auth.api.app:create_app --factory --output openapi.json
        """,
    )

    parser.add_argument(
        "app",
        help='Application import string in format "module:attribute" (e.g., "main:app" or "myapp.api:create_app")',
    )
    parser.add_argument(
        "--factory",
        action="store_true",
        help="Treat the imported object as a factory function and call it to get the app instance",
    )
    parser.add_argument(
        "--output",
        default="openapi.json",
        help="Output file path for the OpenAPI schema (default: openapi.json)",
    )

    args = parser.parse_args()

    try:
        export_openapi_schema(args.app, args.output, args.factory)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
