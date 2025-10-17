
# pyportfolio

Python toolbox to manage your personal portfolio

## Console app

TODO

## Streamlit Web app

Run the Streamlit app with:

```sh
streamlit run app.py
```

Streamlit automatically detects the pages/ folder
and adds a navigation sidebar like this:

🏠 Home
📊 Instruments
💼 Trades
💸 Dividends and Taxes
⚙️ Settings


Each Python file in pages/ is a separate Streamlit script,
executed independently but sharing the same session state.

You can control the order with a numeric prefix (1_, 2_, …)
and use emojis in filenames for icons.


# Lessons learned

## st.tabs

Tabs are a pain in the ass. One of the major drawbacks from using it is that, at the moment, there's no way to programmatically set the active tab.