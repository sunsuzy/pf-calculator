import streamlit as st
import pandas as pd
from fuzzywuzzy import process

def convert_nett_price(value):
    if isinstance(value, str):
        value = value.replace(',', '.')
        return float(value)
    return value

def calculate_total_print_cost(selected_print, quantity, number_of_colors):
    setup_charge = float(selected_print['SetupCharge'].values[0])
    deco_price_from_qty = selected_print['decoPriceFromQty'].values
    deco_price = selected_print['decoPrice'].values

    selected_print = selected_print.sort_values(by='decoPriceFromQty')

    applicable_deco_price_from_qty = None
    applicable_deco_price = None

    for i in range(len(deco_price_from_qty)):
        if quantity >= int(deco_price_from_qty[i]):
            applicable_deco_price_from_qty = int(deco_price_from_qty[i])
            applicable_deco_price = float(deco_price[i].replace(',', '.'))
        else:
            break

    if applicable_deco_price_from_qty is None:
        applicable_deco_price_from_qty = int(deco_price_from_qty[-1])
        applicable_deco_price = float(deco_price[-1].replace(',', '.'))

    total_print_cost = setup_charge + quantity * applicable_deco_price
    return total_print_cost

def main():
    st.title("PF Pricing Calculator")

    product_price_feed_df = pd.read_csv("https://raw.githubusercontent.com/sunsuzy/pf-calculator/master/product%20price%20feed.csv", delimiter=';', dtype={'priceBar': 'str', 'nettPrice': 'object'}, low_memory=False)
    print_price_feed_df = pd.read_csv("https://raw.githubusercontent.com/sunsuzy/pf-calculator/master/Print%20price%20feed.csv", delimiter=';', low_memory=False)

    product_price_feed_df['nettPrice'] = product_price_feed_df['nettPrice'].apply(convert_nett_price)

    descriptions = product_price_feed_df['description'].unique()
    query = st.text_input('Search for a product or enter an item code')
    if query.isdigit():  # If the query is a number, treat it as an item code
        matched_items = product_price_feed_df[product_price_feed_df['itemcode'].astype(str) == str(query)]
        if not matched_items.empty:
            descriptions = [matched_items['description'].values[0]]
        else:
            descriptions = []
    else:  # Otherwise, treat it as a product description
        if query:  # Only do the fuzzy match if the search string is not empty
            closest_matches = process.extract(query, descriptions, limit=10)
            descriptions = [match[0] for match in closest_matches]
        else:
            descriptions = []
    description = st.selectbox('Select a product', descriptions)
    
    matched_products = product_price_feed_df[product_price_feed_df['description'] == description]
    if not matched_products.empty:
        item_code = matched_products['itemcode'].values[0]
        st.write(f"Item Code: {item_code}")

        selected_product = product_price_feed_df[product_price_feed_df['itemcode'] == item_code].copy()

        available_print_techniques = selected_product['decoCharge'].values[0].split(',')
        print_technique = st.selectbox('Select a print technique', available_print_techniques)

        selected_print_technique = print_price_feed_df[print_price_feed_df['printCode'] == print_technique]

        print_technique_name = selected_print_technique['impMethod'].values[0]
        st.write(f"Print Technique: {print_technique_name}")

        available_colors = selected_print_technique['amountColorsId'].unique()
        available_colors = [str(color) for color in available_colors]
        print_colors = st.selectbox('Enter the number of print colors', available_colors)

        quantity = st.number_input('Enter quantity', min_value=1)

        selected_product['priceBar'] = selected_product['priceBar'].astype(int)

        applicable_price_bar = selected_product[selected_product['priceBar'] <= quantity]['priceBar'].max()
        applicable_nett_price = selected_product.loc[selected_product['priceBar'] == applicable_price_bar, 'nettPrice'].values[0]

        total_product_cost = quantity * applicable_nett_price

        selected_print = selected_print_technique[selected_print_technique['amountColorsId'] == print_colors]

        if print_colors == "Full color":
            number_of_colors = None
        else:
            number_of_colors = int(print_colors)

        total_print_cost = calculate_total_print_cost(selected_print, quantity, number_of_colors)

        total_cost_excl_shipping = total_product_cost + total_print_cost
        shipping_cost = 18 if total_cost_excl_shipping < 620 else 0
        total_cost_incl_shipping = total_cost_excl_shipping + shipping_cost

        cost_price = total_cost_excl_shipping / quantity

        margin = st.slider('Enter margin (0-100)', min_value=0, max_value=100, value=50)

        sell_price = cost_price / (1 - (margin / 100))

        cost_breakdown_data = {
            'Cost Component': ['Productkosten', 'Decoratiekosten (inclusief setup)', 'Totaal excl. verzending', 'Verzendkosten', 'Totaal'],
            'Amount': [total_product_cost, total_print_cost, total_cost_excl_shipping, shipping_cost, total_cost_incl_shipping]
        }

        cost_breakdown_df = pd.DataFrame(cost_breakdown_data)
        cost_breakdown_df['Amount'] = cost_breakdown_df['Amount'].apply(lambda x: '€ {:.2f}'.format(x))

        st.write('Kostenoverzicht:')
        st.table(cost_breakdown_df)
        
        st.markdown(f"**Verkoopprijs: € {sell_price:.2f}**")
    else:
        st.write('No matching products found.')

if __name__ == "__main__":
    main()
