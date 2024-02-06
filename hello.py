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
        return  # Exit if data failed to load

    product_price_feed_df = preprocess_data(product_price_feed_df)

    # Product search and selection
    descriptions = product_price_feed_df['description'].unique()
    query = st.text_input('Search for a product or enter an item code')
    selected_product = None

    if query:
        matched_items = product_price_feed_df[product_price_feed_df['itemcode'].astype(str).str.contains(query, case=False) | product_price_feed_df['description'].str.contains(query, case=False)]
        if not matched_items.empty:
            description = st.selectbox('Select a product', matched_items['description'].unique())
            selected_product = matched_items[matched_items['description'] == description].iloc[0]

    if selected_product is not None:
        st.write(f"Selected Product: {selected_product['description']}")

        # Assuming a function to fetch available print techniques for the selected product
        available_print_techniques = [(row['printCode'], row['impMethod']) for index, row in print_price_feed_df.iterrows()]

        if available_print_techniques:
            selected_techniques = st.multiselect('Select print techniques', options=available_print_techniques, format_func=lambda x: f"{x[0]} - {x[1]}")

            decorations_info = []
            for technique, _ in selected_techniques:
                st.write(f"Configuring {technique}:")
                # Example logic to get color options for the selected technique
                # This needs adjustment to match your actual data and logic
                color_options = ['1', '2', '3', '4']  # Placeholder for actual options
                selected_color = st.selectbox(f'Number of colors for {technique}', options=color_options, key=f"colors_{technique}")
                num_colors = int(selected_color)
                # Assuming selected_print_technique is correctly fetched based on 'technique'
                selected_print_technique = print_price_feed_df[print_price_feed_df['printCode'] == technique].iloc[0]
                cost = calculate_total_print_cost(selected_print_technique, 100, num_colors)  # Placeholder quantity
                decorations_info.append({'technique': technique, 'num_colors': num_colors, 'cost': cost})

            # Display decoration info (This is a simplified representation)
            for info in decorations_info:
                st.write(f"Technique: {info['technique']}, Colors: {info['num_colors']}, Cost: €{info['cost']}")

            # Further logic for displaying product cost, total decoration cost, etc.
            # This part of the code would calculate and display other costs as needed
        else:
            st.write("No print techniques available for the selected product.")
    else:
        st.write("Please search for and select a product.")

if __name__ == "__main__":
    main()
