
# pyportfolio

Python toolbox to manage your personal portfolio


## Streamlit

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