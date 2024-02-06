import streamlit as st
import pandas as pd
from fuzzywuzzy import process

def convert_nett_price(value):
    if isinstance(value, str):
        value = value.replace(',', '.')
        return float(value)
    return value

def calculate_total_print_cost(selected_print, quantity, num_colors):
    try:
        setup_charge = convert_nett_price(selected_print['SetupCharge'].values[0])
        deco_price = convert_nett_price(selected_print[selected_print['amountColorsId'].astype(str) == str(num_colors)]['decoPrice'].values[0])
        total_print_cost = setup_charge + (deco_price * quantity)
        return total_print_cost
    except IndexError:  # Handling cases where specific color count is not available
        return 0

def load_data():
    try:
        product_price_feed_df = pd.read_csv("https://raw.githubusercontent.com/sunsuzy/pf-calculator/master/product_price_feed.csv", delimiter=',', dtype={'priceBar': 'str', 'nettPrice': 'object'}, low_memory=False)
        print_price_feed_df = pd.read_csv("https://raw.githubusercontent.com/sunsuzy/pf-calculator/master/Print%20price%20feed.csv", delimiter=',', low_memory=False)
        return product_price_feed_df, print_price_feed_df
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return None, None

def preprocess_data(product_price_feed_df):
    if product_price_feed_df is not None:
        product_price_feed_df['nettPrice'] = product_price_feed_df['nettPrice'].apply(convert_nett_price)
        product_price_feed_df['priceBar'] = product_price_feed_df['priceBar'].apply(pd.to_numeric, errors='coerce')
    return product_price_feed_df
def main():
    st.title("PF Pricing Calculator")

    product_price_feed_df, print_price_feed_df = load_data()
    if product_price_feed_df is None or print_price_feed_df is None:
        return

    product_price_feed_df = preprocess_data(product_price_feed_df)
    descriptions = product_price_feed_df['description'].unique()
    query = st.text_input('Search for a product or enter an item code')

    if query:
        matched_items = product_price_feed_df[product_price_feed_df['itemcode'].str.contains(query, case=False) | product_price_feed_df['description'].str.contains(query, case=False)]
        if not matched_items.empty:
            description = st.selectbox('Select a product', matched_items['description'].unique())
            selected_product = matched_items[matched_items['description'] == description].iloc[0]

            # Display selected product information
            st.write(f"Selected Product: {selected_product['description']}")

            # Filter print techniques based on the selected product
            available_techniques = selected_product['decoCharge'].split(',')
            filtered_print_techniques = print_price_feed_df[print_price_feed_df['printCode'].isin(available_techniques)]

            available_print_techniques = [(row['printCode'], row['impMethod']) for index, row in filtered_print_techniques.iterrows()]
            selected_techniques = st.multiselect('Select print techniques', options=available_print_techniques, format_func=lambda x: f"{x[0]} - {x[1]}")

            for technique, name in selected_techniques:
                # Here you would implement the logic to select the number of colors and calculate cost
                # similar to the approach suggested, ensuring it matches your specific data and logic
                pass  # Placeholder for technique-specific configuration and cost calculation

            # Further logic for calculating and displaying costs
            # This includes product cost, total decoration cost, and any other relevant costs
        else:
            st.write("No matching products found.")
    else:
        st.write("Please enter a search query.")

if __name__ == "__main__":
    main()
