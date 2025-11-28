
import argparse
import lib.console_handlers as c

def main():

    parser = argparse.ArgumentParser(description="📊 Portfolio Manager CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="Initialize the database")

    loadjson_parser = subparsers.add_parser("load-json", help="Load some Yahoo Finance data")
    loadjson_parser.add_argument("-f", "--file", help="The file to ingest (must be Yahoo Finance JSON format)", required=True)

    loadticker_parser = subparsers.add_parser("load", help="Load a single ticker from Yahoo Finance data")
    loadticker_parser.add_argument("-t", "--ticker", help="The symbol ticker (eg: \"IEGE.MI\")")
    loadticker_parser.add_argument("-d", "--days", help="How many days, starting from today, are we going to retrieve")

    args = parser.parse_args()

    match args.command:
        case "init-db":
            c.handle_init_db()
        case "load-json":
            c.handle_load_json(args)
        case "load":
            c.handle_load_ticker(args)

if __name__ == "__main__":
    main()
