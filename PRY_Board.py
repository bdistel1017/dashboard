import dash
from dash import dcc, html, dash_table, Input, Output, State, callback_context
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import numpy as np
import re
import warnings

# Suppress the dateutil warning
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Initialize the Dash app
app = dash.Dash(__name__)
app.title = "Prysmian Maritime Imports Dashboard"

# Color Palette
COLORS = {
    'night_black': '#191B27',
    'light_blue': '#0093FF',
    'light_gray': '#DCE4F2',
    'dark_gray': '#2D354A',
    'light_green': '#22C70C'
}


# Load and preprocess data
def load_data():
    """Load and preprocess the Excel data"""
    try:
        df = pd.read_excel('PRY_Dash.xlsx', sheet_name='Data')

        # Convert date column to datetime
        df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y', errors='coerce')

        # Create buyer column logic
        def determine_buyer(row):
            shipper = str(row['Shipper Declared']).strip() if pd.notna(row['Shipper Declared']) else ''
            intl_comp = str(row['International Competitor']).strip() if pd.notna(
                row['International Competitor']) else ''
            dom_comp = str(row['Domestic Competitor']).strip() if pd.notna(row['Domestic Competitor']) else ''

            # Remove common suffixes and clean names for comparison
            def clean_name(name):
                return re.sub(r'\b(LTD|LLC|INC|CO|COMPANY|LIMITED|PRIVATE)\b\.?', '', name.upper()).strip()

            shipper_clean = clean_name(shipper)
            intl_clean = clean_name(intl_comp)
            dom_clean = clean_name(dom_comp)

            # Logic: buyer is the one that's NOT the shipper
            if intl_comp and intl_clean != shipper_clean:
                return intl_comp
            elif dom_comp and dom_clean != shipper_clean:
                return dom_comp
            elif intl_comp:
                return intl_comp
            elif dom_comp:
                return dom_comp
            else:
                return 'Unknown'

        df['Buyer'] = df.apply(determine_buyer, axis=1)
        df['Seller'] = df['Shipper Declared']

        # Clean numeric columns
        df['Metric Tons'] = pd.to_numeric(df['Metric Tons'], errors='coerce')
        df['Total calculated value ($)'] = pd.to_numeric(df['Total calculated value ($)'], errors='coerce')
        df['Val/KG ($)'] = pd.to_numeric(df['Val/KG ($)'], errors='coerce')

        # Filter for only the 4 specific HS Codes
        target_hs_codes = ['854442', '854449', '854460', '740311']
        df = df[df['HS Code'].astype(str).isin(target_hs_codes)]

        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()


# Simple date parser for MM/DD/YYYY format
def parse_date_simple(date_string):
    """Parse MM/DD/YYYY format only"""
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string.strip(), '%m/%d/%Y').date()
    except:
        return None


# Load data
df = load_data()

# Custom CSS styling
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            body {
                font-family: 'Montserrat', sans-serif;
                font-weight: 300;
                background-color: #191B27;
                color: #DCE4F2;
                margin: 0;
                padding: 0;
            }
            .main-header {
                background: linear-gradient(135deg, #191B27 0%, #191B27 100%);
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            .header-left {
                display: flex;
                align-items: center;
            }
            .logo {
                height: 50px;
                margin-right: 20px;
            }
            .filter-container {
                background-color: #191B27;
                border-radius: 12px;
                padding: 20px;
                margin: 10px 0;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            }
            .metric-card {
                background: linear-gradient(135deg, #2D354A 0%, #191B27 100%);
                border-radius: 12px;
                padding: 20px;
                margin: 10px;
                text-align: center;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
                border: 1px solid #0093FF;
            }
            .chart-container {
                background-color: #191B27;
                border-radius: 12px;
                padding: 20px;
                margin: 10px 0;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            }
            .action-button {
                background-color: #0093FF;
                color: #DCE4F2;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 700;
                font-family: 'Montserrat', sans-serif;
                margin: 5px;
            }
            .action-button:hover {
                background-color: #22C70C;
            }
            .reset-button {
                background-color: #22C70C;
                color: #191B27;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
                font-weight: 600;
                font-family: 'Montserrat', sans-serif;
                margin-left: 10px;
                flex-shrink: 0;
            }
            .reset-button:hover {
                background-color: #1E8E00;
            }
            .global-reset {
                background-color: #22C70C;
                color: #191B27;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 700;
                font-size: 16px;
                font-family: 'Montserrat', sans-serif;
                margin: 10px;
            }
            .global-reset:hover {
                background-color: #1E8E00;
            }
            .filter-row {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                gap: 15px;
                margin-bottom: 20px;
            }
            .filter-item {
                flex: 1;
                min-width: 0;
            }
            .filter-item label {
                display: block;
                margin-bottom: 8px;
                font-weight: 400;
            }
            .filter-input-container {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .date-input {
                flex: 1;
                padding: 10px;
                border-radius: 8px;
                border: 2px solid #2D354A;
                background-color: #2D354A;
                color: #DCE4F2;
                font-size: 14px;
                font-family: 'Montserrat', sans-serif;
                font-weight: 300;
            }
            .date-input::placeholder {
                color: #DCE4F2;
                opacity: 0.7;
            }

            /* Dropdown Styling */
            .Select-control {
                background-color: #2D354A !important;
                border: 2px solid #2D354A !important;
                color: #DCE4F2 !important;
                font-family: 'Montserrat', sans-serif !important;
                font-weight: 300 !important;
            }
            .Select-placeholder, .Select-input > input, .Select-value-label {
                color: #DCE4F2 !important;
                font-family: 'Montserrat', sans-serif !important;
                font-weight: 300 !important;
            }
            .Select-menu-outer {
                background-color: #2D354A !important;
                border: 1px solid #0093FF !important;
            }
            .Select-option {
                background-color: #2D354A !important;
                color: #DCE4F2 !important;
                padding: 8px 12px !important;
                font-family: 'Montserrat', sans-serif !important;
                font-weight: 300 !important;
            }
            .Select-option:hover, .Select-option.is-focused {
                background-color: #0093FF !important;
                color: #DCE4F2 !important;
            }
            .Select-option.is-selected {
                background-color: #22C70C !important;
                color: #191B27 !important;
            }

            /* Modern React-Select Styling */
            .css-1wa3eu0-placeholder, .css-1uccc91-singleValue, .css-g1d714-ValueContainer {
                color: #DCE4F2 !important;
                font-family: 'Montserrat', sans-serif !important;
                font-weight: 300 !important;
            }
            .css-1pahdxg-control {
                background-color: #2D354A !important;
                border: 2px solid #2D354A !important;
                box-shadow: none !important;
            }
            .css-1pahdxg-control:hover {
                border-color: #0093FF !important;
            }
            .css-26l3qy-menu {
                background-color: #2D354A !important;
                border: 1px solid #0093FF !important;
            }
            .css-9jq23d {
                background-color: #2D354A !important;
                color: #DCE4F2 !important;
                font-family: 'Montserrat', sans-serif !important;
                font-weight: 300 !important;
            }
            .css-9jq23d:hover {
                background-color: #0093FF !important;
                color: #DCE4F2 !important;
            }
            .css-g1d714-ValueContainer input {
                color: #DCE4F2 !important;
                font-family: 'Montserrat', sans-serif !important;
                font-weight: 300 !important;
            }

            h1, h2, h3, h4, h5, h6 {
                font-family: 'Montserrat', sans-serif;
                font-weight: 300;
            }

            p, span, div {
                font-family: 'Montserrat', sans-serif;
                font-weight: 300;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Layout
app.layout = html.Div([
    # Main Header with Logo and Global Reset
    html.Div([
        html.Div([
            # Prysmian Logo
            html.Img(src='data:image/png;base64,{}'.format(
                __import__('base64').b64encode(open('PRY_Logo.png', 'rb').read()).decode()
            ), className='logo', style={'height': '50px', 'marginRight': '20px'}),
            html.H1("Maritime Imports Dashboard",
                    style={'color': COLORS['light_gray'], 'fontSize': '36px',
                           'fontWeight': '300', 'margin': '0', 'fontFamily': 'Montserrat'})
        ], className='header-left'),
        html.Button("🔄 Reset All Filters", id="global-reset-btn", className="global-reset")
    ], className='main-header'),

    # Filters Section
    html.Div([
        html.H3("📊 Filters", style={'color': COLORS['light_blue'], 'marginBottom': '20px',
                                    'fontFamily': 'Montserrat', 'fontWeight': '300'}),

        # All Filters in One Row - Evenly Spaced with Consistent Reset Button Placement
        html.Div([
            # Start Date
            html.Div([
                html.Label("Start Date", style={'color': COLORS['light_gray'], 'fontWeight': '400'}),
                html.Div([
                    dcc.Input(
                        id='start-date',
                        type='text',
                        value='',
                        placeholder='MM/DD/YYYY',
                        className='date-input'
                    ),
                    html.Button("Reset", id="start-date-reset", className="reset-button"),
                ], className='filter-input-container')
            ], className='filter-item'),

            # End Date
            html.Div([
                html.Label("End Date", style={'color': COLORS['light_gray'], 'fontWeight': '400'}),
                html.Div([
                    dcc.Input(
                        id='end-date',
                        type='text',
                        value='',
                        placeholder='MM/DD/YYYY',
                        className='date-input'
                    ),
                    html.Button("Reset", id="end-date-reset", className="reset-button"),
                ], className='filter-input-container')
            ], className='filter-item'),

            # Buyer
            html.Div([
                html.Label("Buyer", style={'color': COLORS['light_gray'], 'fontWeight': '400'}),
                html.Div([
                    dcc.Dropdown(
                        id='buyer-filter',
                        options=[],
                        value=None,
                        placeholder='Select buyer...',
                        searchable=True,
                        clearable=True,
                        style={'flex': '1'}
                    ),
                    html.Button("Reset", id="buyer-reset", className="reset-button"),
                ], className='filter-input-container')
            ], className='filter-item'),

            # Seller
            html.Div([
                html.Label("Seller", style={'color': COLORS['light_gray'], 'fontWeight': '400'}),
                html.Div([
                    dcc.Dropdown(
                        id='seller-filter',
                        options=[],
                        value=None,
                        placeholder='Select seller...',
                        searchable=True,
                        clearable=True,
                        style={'flex': '1'}
                    ),
                    html.Button("Reset", id="seller-reset", className="reset-button"),
                ], className='filter-input-container')
            ], className='filter-item'),

            # HS Code
            html.Div([
                html.Label("HS Code", style={'color': COLORS['light_gray'], 'fontWeight': '400'}),
                html.Div([
                    dcc.Dropdown(
                        id='hs-code-filter',
                        options=[],
                        value=None,
                        placeholder='Select HS Code...',
                        searchable=True,
                        clearable=True,
                        style={'flex': '1'}
                    ),
                    html.Button("Reset", id="hs-reset", className="reset-button"),
                ], className='filter-input-container')
            ], className='filter-item'),

            # Country
            html.Div([
                html.Label("Country", style={'color': COLORS['light_gray'], 'fontWeight': '400'}),
                html.Div([
                    dcc.Dropdown(
                        id='country-filter',
                        options=[],
                        value=None,
                        placeholder='Select Country...',
                        searchable=True,
                        clearable=True,
                        style={'flex': '1'}
                    ),
                    html.Button("Reset", id="country-reset", className="reset-button"),
                ], className='filter-input-container')
            ], className='filter-item'),

            # Category
            html.Div([
                html.Label("Category", style={'color': COLORS['light_gray'], 'fontWeight': '400'}),
                html.Div([
                    dcc.Dropdown(
                        id='category-filter',
                        options=[],
                        value=None,
                        placeholder='Select Category...',
                        searchable=True,
                        clearable=True,
                        style={'flex': '1'}
                    ),
                    html.Button("Reset", id="category-reset", className="reset-button"),
                ], className='filter-input-container')
            ], className='filter-item'),
        ], className='filter-row'),

        # Apply Buttons Row
        html.Div([
            html.Button("📅 Apply Date Filter", id="date-go-btn", className="action-button"),
            html.Button("👤 Apply Buyer Filter", id="buyer-go-btn", className="action-button"),
            html.Button("🏭 Apply Seller Filter", id="seller-go-btn", className="action-button"),
            html.Button("📋 Apply HS Filter", id="hs-go-btn", className="action-button"),
            html.Button("🌍 Apply Country Filter", id="country-go-btn", className="action-button"),
            html.Button("📦 Apply Category Filter", id="category-go-btn", className="action-button"),
        ], style={'textAlign': 'center', 'marginTop': '15px'})
    ], className='filter-container'),

    # Key Metrics Row - RIGHT BELOW FILTERS
    html.Div(id='metrics-row', style={'margin': '20px 0'}),

    # Charts Section - ALL AT THE BOTTOM
    html.Div([
        # Volume Chart
        html.Div([
            dcc.Graph(id='volume-chart')
        ], className='chart-container'),

        # Value Chart
        html.Div([
            dcc.Graph(id='value-chart')
        ], className='chart-container'),

        # Category Chart
        html.Div([
            dcc.Graph(id='category-chart')
        ], className='chart-container'),

        # Country Chart
        html.Div([
            dcc.Graph(id='country-chart')
        ], className='chart-container'),

        # Time Series Chart
        html.Div([
            dcc.Graph(id='time-series-chart')
        ], className='chart-container'),

        # Data Table
        html.Div([
            html.H3("📋 Transaction Details", style={'color': COLORS['light_blue'], 'marginBottom': '20px',
                                                    'fontFamily': 'Montserrat', 'fontWeight': '300'}),
            dash_table.DataTable(
                id='data-table',
                columns=[],
                data=[],
                style_cell={
                    'backgroundColor': COLORS['night_black'],
                    'color': COLORS['light_gray'],
                    'border': f'1px solid {COLORS["dark_gray"]}',
                    'textAlign': 'left',
                    'padding': '10px',
                    'fontSize': '12px',
                    'fontFamily': 'Montserrat'
                },
                style_header={
                    'backgroundColor': COLORS['dark_gray'],
                    'color': COLORS['light_blue'],
                    'fontWeight': '600',
                    'border': f'1px solid {COLORS["light_blue"]}',
                    'fontFamily': 'Montserrat'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': COLORS['dark_gray']
                    }
                ],
                page_size=15,
                sort_action='native',
                filter_action='native'
            )
        ], className='chart-container')
    ])
], style={'backgroundColor': COLORS['night_black'], 'minHeight': '100vh', 'padding': '0 20px'})


# Global Reset Callback - FIXED TO WORK PROPERLY
@app.callback(
    [Output('start-date', 'value'),
     Output('end-date', 'value'),
     Output('buyer-filter', 'value'),
     Output('seller-filter', 'value'),
     Output('hs-code-filter', 'value'),
     Output('country-filter', 'value'),
     Output('category-filter', 'value')],
    [Input('global-reset-btn', 'n_clicks'),
     Input('start-date-reset', 'n_clicks'),
     Input('end-date-reset', 'n_clicks'),
     Input('buyer-reset', 'n_clicks'),
     Input('seller-reset', 'n_clicks'),
     Input('hs-reset', 'n_clicks'),
     Input('country-reset', 'n_clicks'),
     Input('category-reset', 'n_clicks')],
    [State('start-date', 'value'),
     State('end-date', 'value'),
     State('buyer-filter', 'value'),
     State('seller-filter', 'value'),
     State('hs-code-filter', 'value'),
     State('country-filter', 'value'),
     State('category-filter', 'value')],
    prevent_initial_call=True
)
def handle_resets(global_reset, start_reset, end_reset, buyer_reset, seller_reset,
                  hs_reset, country_reset, category_reset,
                  start_val, end_val, buyer_val, seller_val, hs_val, country_val, category_val):
    ctx = callback_context
    if not ctx.triggered:
        return '', '', None, None, None, None, None

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Use the current values, defaulting to empty/None if they don't exist
    current_start = start_val if start_val else ''
    current_end = end_val if end_val else ''
    current_buyer = buyer_val
    current_seller = seller_val
    current_hs = hs_val
    current_country = country_val
    current_category = category_val

    if button_id == 'global-reset-btn':
        return '', '', None, None, None, None, None
    elif button_id == 'start-date-reset':
        return '', current_end, current_buyer, current_seller, current_hs, current_country, current_category
    elif button_id == 'end-date-reset':
        return current_start, '', current_buyer, current_seller, current_hs, current_country, current_category
    elif button_id == 'buyer-reset':
        return current_start, current_end, None, current_seller, current_hs, current_country, current_category
    elif button_id == 'seller-reset':
        return current_start, current_end, current_buyer, None, current_hs, current_country, current_category
    elif button_id == 'hs-reset':
        return current_start, current_end, current_buyer, current_seller, None, current_country, current_category
    elif button_id == 'country-reset':
        return current_start, current_end, current_buyer, current_seller, current_hs, None, current_category
    elif button_id == 'category-reset':
        return current_start, current_end, current_buyer, current_seller, current_hs, current_country, None

    return current_start, current_end, current_buyer, current_seller, current_hs, current_country, current_category


# Progressive Filtering - Update dropdown options with AUTO-POPULATE for single options
@app.callback(
    [Output('buyer-filter', 'options'),
     Output('seller-filter', 'options'),
     Output('hs-code-filter', 'options'),
     Output('country-filter', 'options'),
     Output('category-filter', 'options')],
    [Input('date-go-btn', 'n_clicks'),
     Input('buyer-go-btn', 'n_clicks'),
     Input('seller-go-btn', 'n_clicks'),
     Input('hs-go-btn', 'n_clicks'),
     Input('country-go-btn', 'n_clicks'),
     Input('category-go-btn', 'n_clicks'),
     Input('global-reset-btn', 'n_clicks')],
    [State('start-date', 'value'),
     State('end-date', 'value'),
     State('buyer-filter', 'value'),
     State('seller-filter', 'value'),
     State('hs-code-filter', 'value'),
     State('country-filter', 'value'),
     State('category-filter', 'value')],
    prevent_initial_call=True
)
def update_dropdown_options(date_clicks, buyer_clicks, seller_clicks, hs_clicks,
                            country_clicks, category_clicks, reset_clicks,
                            start_date, end_date, buyer, seller, hs_code, country, category):
    if df.empty:
        return [], [], [], [], []

    # Start with full dataset
    filtered_df = df.copy()

    # Apply date filter if dates are provided
    if start_date:
        start_parsed = parse_date_simple(start_date)
        if start_parsed:
            filtered_df = filtered_df[filtered_df['Date'].dt.date >= start_parsed]

    if end_date:
        end_parsed = parse_date_simple(end_date)
        if end_parsed:
            filtered_df = filtered_df[filtered_df['Date'].dt.date <= end_parsed]

    # Apply other filters progressively
    if buyer:
        filtered_df = filtered_df[filtered_df['Buyer'].astype(str) == str(buyer)]

    if seller:
        filtered_df = filtered_df[filtered_df['Seller'].astype(str) == str(seller)]

    if hs_code:
        filtered_df = filtered_df[filtered_df['HS Code'].astype(str) == str(hs_code)]

    if country:
        filtered_df = filtered_df[filtered_df['Country of Origin'].astype(str) == str(country)]

    if category:
        filtered_df = filtered_df[filtered_df['Category'].astype(str) == str(category)]

    # Generate options based on filtered data
    buyers = filtered_df['Buyer'].dropna().unique()
    buyers_str = [str(buyer) for buyer in buyers if str(buyer) != 'Unknown']
    buyer_options = [{'label': buyer, 'value': buyer} for buyer in sorted(buyers_str)]

    sellers = filtered_df['Seller'].dropna().unique()
    sellers_str = [str(seller) for seller in sellers]
    seller_options = [{'label': seller, 'value': seller} for seller in sorted(sellers_str)]

    # Only show the 4 specific HS codes that exist in filtered data
    target_hs_codes = ['854442', '854449', '854460', '740311']
    available_hs = filtered_df['HS Code'].astype(str).unique()
    hs_codes = [code for code in target_hs_codes if code in available_hs]
    hs_options = [{'label': code, 'value': code} for code in sorted(hs_codes)]

    countries = filtered_df['Country of Origin'].dropna().unique()
    countries_str = [str(country) for country in countries]
    country_options = [{'label': country, 'value': country} for country in sorted(countries_str)]

    categories = filtered_df['Category'].dropna().unique()
    categories_str = [str(cat) for cat in categories]
    category_options = [{'label': cat, 'value': cat} for cat in sorted(categories_str)]

    return buyer_options, seller_options, hs_options, country_options, category_options


# Main Dashboard Update Callback
@app.callback(
    [Output('metrics-row', 'children'),
     Output('volume-chart', 'figure'),
     Output('value-chart', 'figure'),
     Output('category-chart', 'figure'),
     Output('country-chart', 'figure'),
     Output('time-series-chart', 'figure'),
     Output('data-table', 'columns'),
     Output('data-table', 'data')],
    [Input('date-go-btn', 'n_clicks'),
     Input('buyer-go-btn', 'n_clicks'),
     Input('seller-go-btn', 'n_clicks'),
     Input('hs-go-btn', 'n_clicks'),
     Input('country-go-btn', 'n_clicks'),
     Input('category-go-btn', 'n_clicks'),
     Input('global-reset-btn', 'n_clicks')],
    [State('start-date', 'value'),
     State('end-date', 'value'),
     State('buyer-filter', 'value'),
     State('seller-filter', 'value'),
     State('hs-code-filter', 'value'),
     State('country-filter', 'value'),
     State('category-filter', 'value')]
)
def update_dashboard(date_clicks, buyer_clicks, seller_clicks, hs_clicks,
                     country_clicks, category_clicks, reset_clicks,
                     start_date, end_date, buyer, seller, hs_code, country, category):
    if df.empty:
        return [html.Div("No data available")], {}, {}, {}, {}, {}, [], []

    # Filter data
    filtered_df = df.copy()

    # Date filtering with simple MM/DD/YYYY parsing
    if start_date:
        start_parsed = parse_date_simple(start_date)
        if start_parsed:
            filtered_df = filtered_df[filtered_df['Date'].dt.date >= start_parsed]

    if end_date:
        end_parsed = parse_date_simple(end_date)
        if end_parsed:
            filtered_df = filtered_df[filtered_df['Date'].dt.date <= end_parsed]

    # Apply other filters
    if buyer:
        filtered_df = filtered_df[filtered_df['Buyer'].astype(str) == str(buyer)]

    if seller:
        filtered_df = filtered_df[filtered_df['Seller'].astype(str) == str(seller)]

    if hs_code:
        filtered_df = filtered_df[filtered_df['HS Code'].astype(str) == str(hs_code)]

    if country:
        filtered_df = filtered_df[filtered_df['Country of Origin'].astype(str) == str(country)]

    if category:
        filtered_df = filtered_df[filtered_df['Category'].astype(str) == str(category)]

    # Calculate metrics
    total_transactions = len(filtered_df)
    total_value = filtered_df['Total calculated value ($)'].sum()
    total_volume = filtered_df['Metric Tons'].sum()
    avg_price_per_kg = filtered_df['Val/KG ($)'].mean()

    # Create metrics cards
    metrics = html.Div([
        html.Div([
            html.H3(f"{total_transactions:,}",
                    style={'color': COLORS['light_blue'], 'fontSize': '28px', 'margin': '0'}),
            html.P("Total Transactions", style={'color': COLORS['light_gray'], 'margin': '5px 0'})
        ], className='metric-card', style={'width': '22%', 'display': 'inline-block'}),

        html.Div([
            html.H3(f"${total_value:,.0f}", style={'color': COLORS['light_green'], 'fontSize': '28px', 'margin': '0'}),
            html.P("Total Value", style={'color': COLORS['light_gray'], 'margin': '5px 0'})
        ], className='metric-card', style={'width': '22%', 'display': 'inline-block'}),

        html.Div([
            html.H3(f"{total_volume:,.1f}", style={'color': COLORS['light_blue'], 'fontSize': '28px', 'margin': '0'}),
            html.P("Metric Tons", style={'color': COLORS['light_gray'], 'margin': '5px 0'})
        ], className='metric-card', style={'width': '22%', 'display': 'inline-block'}),

        html.Div([
            html.H3(f"${avg_price_per_kg:.2f}" if not pd.isna(avg_price_per_kg) else "N/A",
                    style={'color': COLORS['light_green'], 'fontSize': '28px', 'margin': '0'}),
            html.P("Avg Price/KG", style={'color': COLORS['light_gray'], 'margin': '5px 0'})
        ], className='metric-card', style={'width': '22%', 'display': 'inline-block'})
    ])

    # Chart template
    def get_chart_layout(title):
        return {
            'plot_bgcolor': COLORS['night_black'],
            'paper_bgcolor': COLORS['night_black'],
            'font': {'color': COLORS['light_gray'], 'family': 'Montserrat'},
            'title': {'text': title, 'font': {'color': COLORS['light_blue'], 'size': 18, 'family': 'Montserrat'}},
            'xaxis': {'gridcolor': COLORS['dark_gray']},
            'yaxis': {'gridcolor': COLORS['dark_gray']}
        }

    # Volume by Buyer Chart
    if not filtered_df.empty:
        top_buyers = filtered_df.groupby('Buyer')['Metric Tons'].sum().nlargest(10)
        volume_fig = px.bar(
            x=top_buyers.values,
            y=top_buyers.index,
            orientation='h',
            title="Top 10 Buyers by Volume",
            color=top_buyers.values,
            color_continuous_scale=[[0, COLORS['dark_gray']], [1, COLORS['light_blue']]]
        )
        volume_fig.update_layout(get_chart_layout("🏭 Top 10 Buyers by Volume"))
    else:
        volume_fig = go.Figure()
        volume_fig.update_layout(get_chart_layout("🏭 Top 10 Buyers by Volume"))

    # Value by Seller Chart
    if not filtered_df.empty:
        top_sellers = filtered_df.groupby('Seller')['Total calculated value ($)'].sum().nlargest(10)
        value_fig = px.bar(
            x=top_sellers.values,
            y=top_sellers.index,
            orientation='h',
            title="Top 10 Sellers by Value",
            color=top_sellers.values,
            color_continuous_scale=[[0, COLORS['dark_gray']], [1, COLORS['light_green']]]
        )
        value_fig.update_layout(get_chart_layout("💰 Top 10 Sellers by Value"))
    else:
        value_fig = go.Figure()
        value_fig.update_layout(get_chart_layout("💰 Top 10 Sellers by Value"))

    # Category Distribution - TOP 5 ONLY WITH DISTINCT COLORS (PURPLE INSTEAD OF PINK)
    if not filtered_df.empty:
        category_dist = filtered_df['Category'].value_counts().head(5)

        category_colors = [
            COLORS['light_blue'],
            COLORS['light_green'],
            '#8A2BE2',  # MODERATE PURPLE (instead of pink)
            '#4ECDC4',  # Teal
            '#45B7D1'  # Sky Blue
        ]

        category_fig = px.pie(
            values=category_dist.values,
            names=category_dist.index,
            title="Top 5 Categories Distribution",
            color_discrete_sequence=category_colors
        )
        category_fig.update_layout(get_chart_layout("📦 Top 5 Categories Distribution"))
    else:
        category_fig = go.Figure()
        category_fig.update_layout(get_chart_layout("📦 Top 5 Categories Distribution"))

    # Country Distribution
    if not filtered_df.empty:
        country_dist = filtered_df['Country of Origin'].value_counts().head(10)
        country_fig = px.bar(
            x=country_dist.index,
            y=country_dist.values,
            title="Top 10 Countries by Transaction Count",
            color=country_dist.values,
            color_continuous_scale=[[0, COLORS['dark_gray']], [1, COLORS['light_blue']]]
        )
        country_fig.update_layout(get_chart_layout("🌍 Top 10 Countries by Transaction Count"))
        country_fig.update_xaxes(tickangle=45)
    else:
        country_fig = go.Figure()
        country_fig.update_layout(get_chart_layout("🌍 Top 10 Countries by Transaction Count"))

    # Time Series Chart
    if not filtered_df.empty:
        daily_stats = filtered_df.groupby(filtered_df['Date'].dt.date).agg({
            'Total calculated value ($)': 'sum',
            'Metric Tons': 'sum'
        }).reset_index()

        time_fig = go.Figure()
        time_fig.add_trace(go.Scatter(
            x=daily_stats['Date'],
            y=daily_stats['Total calculated value ($)'],
            mode='lines+markers',
            name='Total Value ($)',
            line=dict(color=COLORS['light_green'], width=3),
            yaxis='y'
        ))

        time_fig.add_trace(go.Scatter(
            x=daily_stats['Date'],
            y=daily_stats['Metric Tons'],
            mode='lines+markers',
            name='Metric Tons',
            line=dict(color=COLORS['light_blue'], width=3),
            yaxis='y2'
        ))

        time_fig.update_layout(
            get_chart_layout("📈 Trade Volume & Value Over Time"),
            yaxis=dict(title='Total Value ($)', side='left', color=COLORS['light_green']),
            yaxis2=dict(title='Metric Tons', side='right', overlaying='y', color=COLORS['light_blue']),
            hovermode='x unified'
        )
    else:
        time_fig = go.Figure()
        time_fig.update_layout(get_chart_layout("📈 Trade Volume & Value Over Time"))

    # Data Table
    if not filtered_df.empty:
        table_columns = [
            {'name': 'Date', 'id': 'Date', 'type': 'datetime'},
            {'name': 'Buyer', 'id': 'Buyer'},
            {'name': 'Seller', 'id': 'Seller'},
            {'name': 'Country', 'id': 'Country of Origin'},
            {'name': 'HS Code', 'id': 'HS Code'},
            {'name': 'Category', 'id': 'Category'},
            {'name': 'Metric Tons', 'id': 'Metric Tons', 'type': 'numeric', 'format': {'specifier': '.2f'}},
            {'name': 'Total Value ($)', 'id': 'Total calculated value ($)', 'type': 'numeric',
             'format': {'specifier': '$,.0f'}},
            {'name': 'Val/KG ($)', 'id': 'Val/KG ($)', 'type': 'numeric', 'format': {'specifier': '$.2f'}}
        ]

        table_data = filtered_df[['Date', 'Buyer', 'Seller', 'Country of Origin', 'HS Code',
                                  'Category', 'Metric Tons', 'Total calculated value ($)', 'Val/KG ($)']].to_dict(
            'records')
    else:
        table_columns = []
        table_data = []

    return metrics, volume_fig, value_fig, category_fig, country_fig, time_fig, table_columns, table_data


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8050))
    app.run(debug=False, host='0.0.0.0', port=port)