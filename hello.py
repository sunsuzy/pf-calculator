import streamlit as st
import pandas as pd
from fuzzywuzzy import process

# Helper function to convert price string to float
def convert_nett_price(value):
    if isinstance(value, str):
        value = value.replace(',', '.')
        return float(value)
    return value

# Function to calculate total print cost
def calculate_total_print_cost(selected_print, quantity, number_of_colors):
    setup_charge = convert_nett_price(selected_print['SetupCharge'].values[0])
    
    # This will find the appropriate price bar and corresponding nett price
    for i in range(4, 0, -1):  # Check priceBar4 to priceBar1
        if quantity >= selected_print[f'priceBar{i}']:
            applicable_nett_price = convert_nett_price(selected_print[f'nettPriceQ{i}'])
            break
    else:
        # If quantity is lower than the smallest priceBar, use priceBar1
        applicable_nett_price = convert_nett_price(selected_print['nettPriceQ1'])

    total_print_cost = setup_charge + (quantity * applicable_nett_price)
    return total_print_cost

# Main application function
def main():
    st.title("PF Pricing Calculator")

    # Update the CSV paths as needed
    product_price_feed_df = pd.read_csv(
        "https://raw.githubusercontent.com/sunsuzy/pf-calculator/master/product%20price%20feed.csv",
        delimiter=',',
        converters={
            'nettPriceQ1': convert_nett_price,
            'nettPriceQ2': convert_nett_price,
            'nettPriceQ3': convert_nett_price,
            'nettPriceQ4': convert_nett_price
        },
        dtype={
            'priceBar1': int,
            'priceBar2': int,
            'priceBar3': int,
            'priceBar4': int
        }
    )

    # Ensure you read the print price feed correctly as well
    print_price_feed_df = pd.read_csv(
        "https://raw.githubusercontent.com/sunsuzy/pf-calculator/master/Print%20price%20feed.csv",
        delimiter=';',
        low_memory=False
    )

    # Convert the price bars and nett prices to numeric values after they have been read
    for i in range(1, 5):
        product_price_feed_df[f'priceBar{i}'] = product_price_feed_df[f'priceBar{i}'].apply(pd.to_numeric, errors='coerce')
        product_price_feed_df[f'nettPriceQ{i}'] = product_price_feed_df[f'nettPriceQ{i}'].apply(convert_nett_price)

    # Additional code here...
    # Search functionality
    descriptions = product_price_feed_df['description'].unique()
    query = st.text_input('Search for a product or enter an item code')
    if query:  # If the query is not empty
        matched_items = product_price_feed_df[product_price_feed_df['itemcode'].astype(str).str.lower() == str(query).lower()]
        if not matched_items.empty:
            descriptions = [matched_items['description'].values[0]]
        else:  # Otherwise, treat it as a product description
            closest_matches = process.extract(query, descriptions, limit=10)
            descriptions = [match[0] for match in closest_matches]

    description = st.selectbox('Select a product', descriptions)
    matched_products = product_price_feed_df[product_price_feed_df['description'] == description]
    
    if not matched_products.empty:
        item_code = matched_products['itemcode'].values[0]
        st.write(f"Item Code: {item_code}")

        # Find and display available print techniques for the selected product
        selected_product = product_price_feed_df[product_price_feed_df['itemcode'] == item_code].copy()
        available_print_techniques = selected_product['decoCharge'].values[0].split(',')
        print_techniques_with_names = []
        for technique in available_print_techniques:
            technique_df = print_price_feed_df[print_price_feed_df['printCode'] == technique]
            if not technique_df.empty:
                print_techniques_with_names.append((technique, technique_df['impMethod'].values[0]))
        print_technique = st.selectbox('Select a print technique', options=print_techniques_with_names, format_func=lambda x: f"{x[0]} - {x[1]}")

        # Process selected print technique
        selected_print_technique = print_price_feed_df[print_price_feed_df['printCode'] == print_technique[0]]

        # Select number of print colors
        available_colors = selected_print_technique['amountColorsId'].unique()
        available_colors = [str(color) for color in available_colors]
        print_colors = st.selectbox('Enter the number of print colors', available_colors)

        # Input for quantity
        quantity = st.number_input('Enter quantity', min_value=1)  # Adjust the min_value as needed

        # Calculate the total product cost based on quantity and nett prices
        # Here we need to refactor the logic to determine the applicable nett price based on quantity
        applicable_price_bar = None
        applicable_nett_price = None
        for i in range(1, 5):
            if quantity >= selected_product[f'priceBar{i}'].values[0]:
                applicable_price_bar = selected_product[f'priceBar{i}'].values[0]
                applicable_nett_price = selected_product[f'nettPriceQ{i}'].values[0]
            else:
                break
        if applicable_nett_price is None:
            st.error('No matching product found for the given quantity.')
            return
        total_product_cost = quantity * applicable_nett_price

        # Select print colors and calculate print cost
        selected_print = selected_print_technique[selected_print_technique['amountColorsId'] == print_colors]
        number_of_colors = int(print_colors) if print_colors.isdigit() else None
        total_print_cost = calculate_total_print_cost(selected_print, quantity, number_of_colors)

        # Calculate the total cost including shipping
        total_cost_excl_shipping = total_product_cost + total_print_cost
        shipping_cost = 18 if total_cost_excl_shipping < 620 else 0
        total_cost_incl_shipping = total_cost_excl_shipping + shipping_cost

        # Calculate selling price with margin
        kostprijs = total_cost_incl_shipping / quantity
        margin = st.slider('Enter margin (0-100)', min_value=0, max_value=100, value=38)
        sell_price = kostprijs / (1 - (margin / 100))

        # Display cost breakdown
        cost_breakdown_data = {
            'Cost Component': ['Productkosten', 'Decoratiekosten (inclusief setup)', 'Totaal excl. verzending', 'Verzendkosten', 'Totaal'],
            'Amount': [total_product_cost, total_print_cost, total_cost_excl_shipping, shipping_cost, total_cost_incl_shipping]
        }
        cost_breakdown_df = pd.DataFrame(cost_breakdown_data)
        cost_breakdown_df['Amount'] = cost_breakdown_df['Amount'].apply(lambda x: '€ {:.2f}'.format(x))

        st.write('Kostenoverzicht:')
        st.table(cost_breakdown_df)

        # Display prices
        st.markdown(f"<p style='color:red'>**Kostprijs: € {kostprijs:.2f}**</p>", unsafe_allow_html=True)
        st.markdown(f"**Verkoopprijs: € {sell_price:.2f}**")
    else:
        st.write('No matching products found.')

if __name__ == "__main__":
    main()
