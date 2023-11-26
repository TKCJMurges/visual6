'''
 # @ Create Time: 2023-11-26 14:46:34.011634
'''
# Importing the necessary files
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.io as pio
from dash import Dash, dcc, html
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd

app = Dash(__name__, title="MyVisual")

# Declare server for Heroku deployment. Needed for Procfile.
server = app.server

# Data loading and preprocessing
stock_data = pd.read_csv("data.csv")
stock_data['Volume'] = pd.to_numeric(stock_data['Volume'].str.replace(',', ''), errors='coerce')

# Convert 'Date' column to datetime format
stock_data['Date'] = pd.to_datetime(stock_data['Date'])

current_time_str = stock_data['Date'].max()
print(current_time_str)
current_time = current_time_str.to_pydatetime()
print(current_time)

# Create a dropdown filter for company selection
companies = stock_data['Name'].unique().tolist()

# Calculate VWAP for each company
stock_data['VWAP'] = (stock_data['Closing_Price'] * stock_data['Volume']).cumsum() / stock_data['Volume'].cumsum()

# Calculate Simple Moving Average (SMA) for Closing_Price (taking a window of 3 days as an example)
stock_data['SMA'] = stock_data['Closing_Price'].rolling(window=3).mean()

# Calculate Bollinger Bands
window = 20  # You can adjust the window size as needed
stock_data['Middle_Band'] = stock_data['Closing_Price'].rolling(
    window=window).mean()
stock_data['Upper_Band'] = stock_data['Middle_Band'] + 2 * stock_data[
    'Closing_Price'].rolling(window=window).std()
stock_data['Lower_Band'] = stock_data['Middle_Band'] - 2 * stock_data[
    'Closing_Price'].rolling(window=window).std()

# Calculate RSI for Closing_Price (taking a window of 14 days as an example)
delta = stock_data['Closing_Price'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
rsi = 100 - (100 / (1 + rs))

# Pivot the stock_dataset to have Date as the index and companies as columns
pivot_stock_data = stock_data.pivot(index='Date',
                                    columns='Name',
                                    values='Closing_Price')

# Calculate correlation matrix
correlation_matrix = pivot_stock_data.corr()

# Calculate quartiles for correlation coefficients
coefficients = correlation_matrix.values.flatten()
lower_quantile = np.percentile(coefficients, 25)
upper_quantile = np.percentile(coefficients, 75)

# Define contours for lower and upper quartiles
contour_lower = go.Contour(
    z=correlation_matrix.values,
    x=correlation_matrix.index,
    y=correlation_matrix.columns,
    contours=dict(start=-1, end=lower_quantile,
                  size=0.05),  # Adjust size as needed
    colorscale='Blues',  # Choose a colorscale for lower quartile contours
    showscale=False,
    name=f'Lower Quartile Contours (-1 - {lower_quantile:.2f})')

contour_upper = go.Contour(
    z=correlation_matrix.values,
    x=correlation_matrix.index,
    y=correlation_matrix.columns,
    contours=dict(start=upper_quantile, end=1,
                  size=0.05),  # Adjust size as needed
    colorscale='Reds',  # Choose a colorscale for upper quartile contours
    showscale=False,
    name=f'Upper Quartile Contours ({upper_quantile:.2f} - 1)')
# Create an empty figure
fig = go.Figure()
fig_rs = go.Figure()
fig_sm = go.Figure()
fig_cs = go.Figure()
fig_bc = go.Figure()
fig_ts = go.Figure()
fig2 = go.Figure()

# Define your layout for each visualization
# Visualization 5 layout
sma_layout = html.Div([
    html.Label('Select Company:'),
    dcc.Dropdown(
        id='company-dropdown_s',
        options=[{
            'label': company,
            'value': company
        } for company in stock_data['Name'].unique()],
        value=stock_data['Name'].iloc[0]  # Default value for dropdown
    ),
    html.Br(),
    html.Label('Select Timeframe:'),
    dcc.RadioItems(id='timeframe-radio_s',
                   options=[{
                       'label': 'Last 1 Month',
                       'value': '1M'
                   }, {
                       'label': 'Last 5 Months',
                       'value': '5M'
                   }, {
                       'label': 'Last 1 Year',
                       'value': '1Y'
                   }, {
                       'label': 'Last 5 Years',
                       'value': '5Y'
                   }, {
                       'label': 'Entire Duration',
                       'value': 'All'
                   }],
                   value='All',
                   labelStyle={'display': 'block'}),
    dcc.Graph(figure = fig_sm, id='sma-chart')
])

# Combine all visualizations vertically
app.layout = html.Div([
    html.H1("Interactive chart"),sma_layout
])

# Define callback to update the SMA chart based on selected company and timeframe
@app.callback(Output('sma-chart', 'figure'), [
    Input('company-dropdown_s', 'value'),
    Input('timeframe-radio_s', 'value')
])
def update_sma_chart(selected_company, selected_timeframe):
  filtered_stock_data = stock_data[stock_data['Name'] == selected_company]

  if selected_timeframe == '1M':
    start_date = current_time - timedelta(days=30)
  elif selected_timeframe == '5M':
    start_date = current_time - timedelta(days=150)
  elif selected_timeframe == '1Y':
    start_date = current_time - timedelta(days=365)
  elif selected_timeframe == '5Y':
    start_date = current_time - timedelta(
        days=1825)  # Approximation of 5 years
  else:
    start_date = filtered_stock_data['Date'].min()  # Entire duration

  filtered_stock_data = filtered_stock_data[
      pd.to_datetime(filtered_stock_data['Date']) >= start_date]

  fig_sm = px.line(filtered_stock_data,
                   x='Date',
                   y=['Closing_Price', 'SMA'],
                   title=f'Simple Moving Average (SMA) for {selected_company}')

  # Handle NaN values in 'SMA' column by replacing them with a default size
  sizes = filtered_stock_data['SMA'].fillna(
      10)  # Replace NaN values with default size 10

  # Add scatter plot for markers and channels
  fig_sm.add_scatter(x=filtered_stock_data['Date'],
                     y=filtered_stock_data['Closing_Price'],
                     mode='markers',
                     marker=dict(size=sizes,
                                 color=filtered_stock_data['SMA'],
                                 colorscale='Viridis',
                                 opacity=0.7,
                                 colorbar=dict(title='SMA'),
                                 line=dict(width=1, color='DarkSlateGrey')),
                     name='Price vs SMA')

  fig_sm.update_traces(
      mode='lines',
      selector=dict(type='scatter'))  # Set lines for main plot lines

  fig_sm.update_layout(
      xaxis=dict(title='Date',
                 tickformat='%Y-%m-%d',
                 showgrid=True,
                 linecolor='black',
                 linewidth=1),
      yaxis=dict(title='Price', showgrid=True, linecolor='black', linewidth=1),
      paper_bgcolor='white',  # Set paper (outside plot area) background color
      font=dict(family='Arial', size=12,
                color='Black')  # Set font style and size
  )
  return fig_sm

# Run the app
if __name__ == '__main__':
  app.run_server(debug=True, port=int(os.environ.get('PORT', 8050)))