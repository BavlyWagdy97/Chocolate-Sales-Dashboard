import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd

# Load dataset
file_name = "Chocolate_Sales.csv"
df = pd.read_csv(f"{file_name}")
df["Amount"] = df["Amount"].replace("[\\$,]", "", regex=True).astype(int)

# Convert the 'Date' column to datetime format
df['Date'] = pd.to_datetime(df['Date'], format="%d-%b-%y", errors='coerce')
df['Year'] = df['Date'].dt.year
df['Month'] = df['Date'].dt.month

# Dataset description
description = html.Div([
    html.B("Source:"), " Kaggle",
    html.Br(),
    "📏 ", html.B("Dataset Shape:"),
    html.Ul([
        html.Li([html.B("Rows:"), f" 1094 " ]),
        html.Li([html.B("Columns:"), f" 6 " ] )
    ]),
    html.Br(),
    "📝 ", html.B("Description"),
    html.P("This dataset contains detailed records of chocolate sales, including product details, sales quantities, revenue, and customer segments. \n It is designed for sales forecasting, trend analysis, and business intelligence,\n  helping businesses optimize pricing strategies, inventory management, and customer targeting."),
    html.Br(),
    "📊 ", html.B("Data Collection Methodology"),
    html.Ul([
        html.Li("Data was aggregated from chocolate retailers and online marketplaces."),
        html.Li("Only confirmed transactions were included to ensure accuracy."),
        html.Li("Revenue values reflect final prices after applying discounts, if any.")
    ])
])

# Insights for bar charts
bar_insights = {
    "Product": df.groupby("Product")["Amount"].sum().idxmax(),
    "Country": df.groupby("Country")["Amount"].sum().idxmax(),
    "Sales Person": df.groupby("Sales Person")["Amount"].sum().idxmax()
}

# Insights for histograms
histogram_insights = {
    "Amount": f"The average sales amount is ${df['Amount'].mean():,.2f}, with most transactions falling around this value. This indicates a consistent sales pattern.",
    "Boxes Shipped": f"The average number of boxes shipped is {df['Boxes Shipped'].mean():,.2f}, with most shipments concentrated around this value, suggesting stable demand."
}

# Function to generate relation insights
def get_relation_insight(chart_type):
    if chart_type == 'country':
        top_country = df.groupby("Country")["Amount"].sum().idxmax()
        top_sales = df.groupby("Country")["Amount"].sum().max()
        return f"Insight: The country with the highest sales is {top_country} with total sales of ${top_sales:,.2f}. This indicates a strong market presence and customer demand in this region."
    elif chart_type == 'product':
        top_product = df.groupby("Product")["Amount"].sum().idxmax()
        top_sales = df.groupby("Product")["Amount"].sum().max()
        return f"Insight: The best-selling product is {top_product} with total sales reaching ${top_sales:,.2f}. This suggests high customer preference and possible opportunities for further marketing of this product."
    elif chart_type == 'salesperson':
        top_salesperson = df.groupby("Sales Person")["Amount"].sum().idxmax()
        top_sales = df.groupby("Sales Person")["Amount"].sum().max()
        return f"Insight: The top-performing salesperson is {top_salesperson}, generating total sales of ${top_sales:,.2f}. Recognizing top performers can help in setting training strategies for other team members."
    elif chart_type == 'monthly':
        peak_month = df.groupby("Month")["Amount"].sum().idxmax()
        return f"Insight: The highest monthly sales occurred in month {peak_month}, indicating seasonal trends that can be leveraged for better inventory and marketing planning."
    return ""

# Function to generate outlier insights
def get_outlier_insight(column):
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)][column]
    if not outliers.empty:
        return f"Insight: Column '{column}' has {len(outliers)} outliers. These extreme values might be due to errors in data entry, special promotions, or unexpected demand spikes."
    return f"Insight: Column '{column}' has no significant outliers, indicating a relatively normal distribution."

# Numeric and categorical columns
numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
numeric_columns = [col for col in numeric_columns if col != 'Year' and col != 'Month']
categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()

# Initialize Dash app with Bootstrap
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

app.layout = dbc.Container([
    html.H1("\ud83d\udcc8 Chocolate Sales Dashboard", className='text-center my-4', style={'font-family': 'Arial, sans-serif'}),
    
    dbc.Tabs(id='tabs', active_tab='data_info', children=[
        dbc.Tab(label='Data Info', tab_id='data_info'),
        dbc.Tab(label='Distributions', tab_id='distributions'),
        dbc.Tab(label='Relations', tab_id='relations'),
        dbc.Tab(label='Box Plot', tab_id='box_plot'),
    ], className='mb-3'),
    
    html.Div(id='tab-content')
], fluid=True)

# Callback to update tab content
@app.callback(
    Output('tab-content', 'children'),
    Input('tabs', 'active_tab')
)
def update_tab(tab_name):
    if tab_name == 'data_info':
        return dbc.Card([
            dbc.CardHeader("Dataset Information", style={'font-size': '18px', 'font-weight': 'bold'}),
            dbc.CardBody([
                html.P(html.Pre(description), style={'font-size': '16px', 'color': '#333'}),
                dash_table.DataTable(
                    data=pd.read_csv(file_name).head().to_dict('records'),
                    columns=[{"name": i, "id": i} for i in pd.read_csv(file_name).columns],
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left', 'padding': '5px'},
                    style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'}
                ),
                html.A("🔗 Kaggle Dataset Link", href="https://www.kaggle.com/datasets/atharvasoundankar/chocolate-sales", target="_blank", style={"font-weight": "bold"})
            ])
        ])
    
    if tab_name == 'distributions':
        return html.Div([
            html.H3("Bar Charts", className='text-center mt-4 mb-3'),
            dcc.Dropdown(
                id='bar-chart-selection',
                options=[
                    {'label': 'Product', 'value': 'Product'},
                    {'label': 'Country', 'value': 'Country'},
                    {'label': 'Sales Person', 'value': 'Sales Person'}
                ],
                value='Product',
                className='mb-3'
            ),
            dcc.Graph(id='bar-chart'),
            html.P(id='bar-insight', className='text-muted', style={'font-style': 'italic', 'text-align': 'center', 'font-weight': 'bold'}),
            
            html.H3("Histograms", className='text-center mt-4 mb-3'),
            dcc.Dropdown(
                id='histogram-selection',
                options=[
                    {'label': 'Amount', 'value': 'Amount'},
                    {'label': 'Boxes Shipped', 'value': 'Boxes Shipped'}
                ],
                value='Amount',
                className='mb-3'
            ),
            dcc.Graph(id='histogram'),
            html.Div(id='histogram-insight', style={'text-align': 'center', 'font-weight': 'bold', 'font-style': 'italic'})
        ])
    
    if tab_name == 'relations':
        return html.Div([
            dcc.Dropdown(
                id='relation-dropdown',
                options=[
                    {'label': 'Total Sales by Country', 'value': 'country'},
                    {'label': 'Best-Selling Chocolate Products', 'value': 'product'},
                    {'label': 'Sales Performance by Salesperson', 'value': 'salesperson'},
                    {'label': 'Monthly Sales Trends Over the Year', 'value': 'monthly'}
                ],
                placeholder='Select a chart',
                value='country'
            ),
            dcc.Graph(id='relation-graph'),
            html.B(id='relation-insight', style={'text-align': 'center', 'font-weight': 'bold'})
        ])
    
    if tab_name == 'box_plot':
        return html.Div([
            dcc.Dropdown(
                id='box-plot-selection',
                options=[{'label': col, 'value': col} for col in numeric_columns],
                placeholder='Select a numeric column for Box Plot'
            ),
            dcc.Graph(id='box-plot-graph'),
            html.B(id='box-plot-insight', className='text-muted', style={'font-style': 'italic', 'text-align': 'center', 'font-weight': 'bold'})
        ])
    
    return ""

# Callback for bar chart
@app.callback(
    [Output('bar-chart', 'figure'), Output('bar-insight', 'children')],
    [Input('bar-chart-selection', 'value')]
)
def update_bar_chart(selected_column):
    fig = px.bar(df.groupby(selected_column)["Amount"].sum().reset_index(), x=selected_column, y='Amount', title=f"Total Sales by {selected_column}", color_discrete_sequence=['#FF6F61'])
    fig.update_layout(
        xaxis_title=dict(text=f"{selected_column}", font=dict(size=14, color='black', weight='bold')),
        yaxis_title=dict(text="Amount", font=dict(size=14, color='black', weight='bold'))
    )
    insight = f"Insight: The highest {selected_column} in sales is {bar_insights[selected_column]} with total sales of ${df.groupby(selected_column)['Amount'].sum().max():,.2f}."
    return fig, insight

# Callback for histogram
@app.callback(
    [Output('histogram', 'figure'), Output('histogram-insight', 'children')],
    [Input('histogram-selection', 'value')]
)
def update_histogram(selected_column):
    fig = px.histogram(df, x=selected_column, title=f"Distribution of {selected_column}", color_discrete_sequence=['#6B8E23'], opacity=0.7)
    fig.update_layout(
        xaxis_title=dict(text=f"{selected_column}", font=dict(size=14, color='black', weight='bold')),
        yaxis_title=dict(text="Count", font=dict(size=14, color='black', weight='bold'))
    )
    insight = histogram_insights[selected_column]
    insight_div = html.Div(insight, style={'text-align': 'center', 'font-weight': 'bold', 'font-style': 'italic'})
    return fig, insight_div

# Callback for relation chart
@app.callback(
    [Output('relation-graph', 'figure'), Output('relation-insight', 'children')],
    [Input('relation-dropdown', 'value')]
)
def update_relation_chart(selected_chart):
    fig = px.scatter()
    insight = ""
    
    if selected_chart == 'country':
        fig = px.bar(df.groupby("Country")["Amount"].sum().reset_index(), x="Country", y="Amount", title="Total Sales by Country")
        fig.update_layout(
            xaxis_title=dict(text="Country", font=dict(size=14, color='black', weight='bold')),
            yaxis_title=dict(text="Amount", font=dict(size=14, color='black', weight='bold'))
        )
    elif selected_chart == 'product':
        fig = px.bar(df.groupby("Product")["Amount"].sum().reset_index(), x="Product", y="Amount", title="Best-Selling Chocolate Products")
        fig.update_layout(
            xaxis_title=dict(text="Product", font=dict(size=14, color='black', weight='bold')),
            yaxis_title=dict(text="Amount", font=dict(size=14, color='black', weight='bold'))
        )
    elif selected_chart == 'salesperson':
        fig = px.bar(df.groupby("Sales Person")["Amount"].sum().reset_index().sort_values(by="Amount", ascending=False), x="Sales Person", y="Amount", title="Sales Performance by Salesperson")
        fig.update_layout(
            xaxis_title=dict(text="Sales Person", font=dict(size=14, color='black', weight='bold')),
            yaxis_title=dict(text="Amount", font=dict(size=14, color='black', weight='bold'))
        )
    elif selected_chart == 'monthly':
        fig = px.line(df.groupby("Month")["Amount"].sum().reset_index(), x="Month", y="Amount", title="Monthly Sales Trends Over the Year")
        fig.update_layout(
            xaxis_title=dict(text="Month", font=dict(size=14, color='black', weight='bold')),
            yaxis_title=dict(text="Amount", font=dict(size=14, color='black', weight='bold'))
        )
    
    insight = get_relation_insight(selected_chart)
    return fig, insight

# Callback for box plot
@app.callback(
    [Output('box-plot-graph', 'figure'), Output('box-plot-insight', 'children')],
    Input('box-plot-selection', 'value')
)
def update_box_plot(selected_column):
    if selected_column:
        fig = px.box(df, y=selected_column, title=f"Box Plot of {selected_column}")
        fig.update_layout(
            yaxis_title=dict(text=f"{selected_column}", font=dict(size=14, color='black', weight='bold'))
        )
        insight = get_outlier_insight(selected_column)
        return fig, insight
    return px.scatter(), ""

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)