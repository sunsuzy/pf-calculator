import streamlit as st
import pandas as pd

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

    product_price_feed_df = pd.read_csv("C:/Users/Sundeep.CSE/Environments/Test/my_env/product price feed.csv", delimiter=';', dtype={'priceBar': 'str', 'nettPrice': 'object'}, low_memory=False)
    print_price_feed_df = pd.read_csv("https://raw.githubusercontent.com/sunsuzy/pf-calculator/master/Print%20price%20feed.csv?token=GHSAT0AAAAAACFI563F2ZMVPVIYWMGQRTJUZFXW3LA", delimiter=';', low_memory=False)

    product_price_feed_df['nettPrice'] = product_price_feed_df['nettPrice'].apply(convert_nett_price)

    descriptions = product_price_feed_df['description'].unique()
    description_query = st.text_input('Search for a product')
    matched_descriptions = [desc for desc in descriptions if description_query.lower() in desc.lower()]
    description = st.selectbox('Select a product', matched_descriptions)

    item_code = product_price_feed_df[product_price_feed_df['description'] == description]['itemcode'].values[0]

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

    total_cost = total_product_cost + total_print_cost

    if total_cost < 620:
        total_cost += 18

    cost_price = total_cost / quantity

    margin = st.slider('Enter margin (0-100)', min_value=0, max_value=100, value=50)

    sell_price = cost_price / (1 - (margin / 100))

    cost_breakdown_data = {
        'Cost Component': ['Product Cost', 'Print Cost', 'Total Cost', 'Cost Price', 'Sell Price'],
        'Amount': [total_product_cost, total_print_cost, total_cost, cost_price, sell_price]
    }

    cost_breakdown_df = pd.DataFrame(cost_breakdown_data)
    cost_breakdown_df['Amount'] = cost_breakdown_df['Amount'].apply(lambda x: '{:.2f}'.format(x))

    st.write('Cost Breakdown:')
    st.table(cost_breakdown_df)

if __name__ == "__main__":
    main()






