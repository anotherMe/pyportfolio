
# pyportfolio

Python - Streamlit app to manage your personal portfolio


## Install

To support latest Streamlit version ( eg: 1.52.0 ), you'll need a quite recent version of Python. Let's say 3.14 should do:

```sh
brew install python@3.14
/opt/homebrew/opt/python@3.14/bin/python3 -m venv .venv
```

Then you can install dependencies:

```sh
source .venv/bin/activate
pip install -r requirements.txt
```


## Run

Run the Streamlit app with:

```sh
source .venv/bin/activate
streamlit run main.py
```

# Lessons learned

## st.tabs

Tabs are a pain in the ass. One of the major drawbacks from using them is that, at the moment, there's no way to programmatically set the active tab.


# Database

All dates / timestamps in the database are ( and must be ) UTC.

