
import argparse
import lib.console_handlers as c

def main():

    parser = argparse.ArgumentParser(description="📊 Portfolio Manager CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="Initialize the database")

    loaddata_parser = subparsers.add_parser("load-data", help="Load some Yahoo Finance data")
    loaddata_parser.add_argument("-f", "--file", help="The file to ingest (must be Yahoo Finance JSON format)", required=True)


    args = parser.parse_args()

    match args.command:
        case "init-db":
            c.handle_init_db()
        case "load-data":
            c.handle_load_data(args)

if __name__ == "__main__":
    main()
