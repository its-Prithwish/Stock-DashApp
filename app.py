import dash
from dash import dcc
from dash import html
from datetime import datetime as dt
import yfinance as yf
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
import plotly.express as px
# model
from model import prediction # Importing prediction function from model.py
from flask import Flask
from gevent.pywsgi import WSGIServer

# Function to generate a plot for displaying closing and opening prices vs date
def get_stock_price_fig(df):

    # Create a line plot using Plotly Express, with 'Date' on the x-axis and 'Close' and 'Open' on the y-axis
    # The plot is titled "Closing and Opening Price vs Date"

    fig = px.line(df,
                  x="Date",
                  y=["Close", "Open"],
                  title="Closing and Openning Price vs Date")

    return fig

# Function to generate a plot for displaying Exponential Moving Average (EWA) vs date
def get_more(df):
    
    # Calculate the Exponential Moving Average (EWA) of closing prices with a span of 20
    df['EWA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    
    # Create a scatter plot using Plotly Express, with 'Date' on the x-axis and 'EWA_20' on the y-axis
    # The plot is titled "Exponential Moving Average vs Date"
    fig = px.scatter(df,
                     x="Date",
                     y="EWA_20",
                     title="Exponential Moving Average vs Date")
    
    # Update the scatter plot to display lines connecting the points and markers at the data points
    fig.update_traces(mode='lines+markers')
    
    return fig

# Initialize Flask server
server = Flask(__name__)

# Initialize Dash app with external stylesheets for improved UI
app = dash.Dash(
    __name__, server=server,
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Roboto&display=swap"
    ])


# HTML layout of the web application
app.layout = html.Div(
    [
        html.Div(
            [
                # Navigation
                html.P("Stock Dash App", className="start"),
                html.Div([
                    html.P("Stock Code: "),
                    html.Div([
                        dcc.Input(id="dropdown_tickers", type="text"),
                        html.Button("Search", id='submit'),
                    ],
                             className="form")
                ],
                         className="input-place"),
                html.Div([
                    dcc.DatePickerRange(id='my-date-picker-range',
                                        min_date_allowed=dt(1995, 8, 5),
                                        max_date_allowed=dt.now(),
                                        initial_visible_month=dt.now(),
                                        end_date=dt.now().date()),
                ],
                         className="date"),
                html.Div([
                    html.Button(
                        "Stock Price", className="stock-btn", id="stock"),
                    html.Button("Indicators",
                                className="indicators-btn bg-white",
                                id="indicators"),
                    dcc.Input(id="n_days",
                              type="text",
                              placeholder="Number of days"),
                    html.Button(
                        "Forecast", className="forecast-btn", id="forecast")
                ],
                         className="buttons"),
            ],
            className="nav"),

        # content
        html.Div(
            [
                html.Div(
                    [  # header
                        html.Img(id="logo"),
                        html.P(id="ticker")
                    ],
                    className="header"),
                html.Div(id="description", className="decription_ticker"),
                html.Div([], id="graphs-content"),
                html.Div([], id="main-content"),
                html.Div([], id="forecast-content")
            ],
            className="content"),
    ],
    className="container")


# Callback for company info
@app.callback([
    Output("description", "children"),
    Output("logo", "src"),
    Output("ticker", "children"),
    Output("stock", "n_clicks"),
    Output("indicators", "n_clicks"),
    Output("forecast", "n_clicks")
], [Input("submit", "n_clicks")], [State("dropdown_tickers", "value")])
def update_data(n, val):  # inpur parameter(s)
    if n == None:
        # Initial message if no stock code is entered
        return "Hey there! Please enter a legitimate stock code to get details.", "./assets/stocks-img.jpg", "Stocks", None, None, None

    else:
        if val == None:
            # Raise PreventUpdate if no stock code is entered
            raise PreventUpdate
        else:
            # Fetching stock information using Yahoo Finance API
            yf.pdr_override()
            ticker = yf.Ticker(val)
            inf = ticker.info
            df = pd.DataFrame().from_dict(inf, orient="index").T
            df[['shortName', 'longBusinessSummary']]
            return df['longBusinessSummary'].values[0], "./assets/stocks-img.jpg", df['shortName'].values[0], None, None, None

# callback for stocks graphs
@app.callback([
    Output("graphs-content", "children"),  # Define the output component for the callback
], [
    Input("stock", "n_clicks"),  # Define the input components for the callback
    Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date')
], [State("dropdown_tickers", "value")])  # Define the state component for the callback
def stock_price(n, start_date, end_date, val):
    if n == None:  # If the "stock" button has not been clicked
        return [""]  # Return an empty list for the children of "graphs-content"

    if val == None:  # If no stock ticker has been selected
        raise PreventUpdate  # Raise PreventUpdate to prevent updating the callback
    else:
        if start_date != None:  # If a start date has been selected
            df = yf.download(val, str(start_date), str(end_date))  # Download data for the selected stock within the specified date range
        else:
            df = yf.download(val)  # Download data for the selected stock without specifying a date range

    df.reset_index(inplace=True)  # Reset the index of the DataFrame
    fig = get_stock_price_fig(df)  # Generate the figure for stock price visualization
    return [dcc.Graph(figure=fig)]  # Return the figure wrapped in a dcc.Graph component for the callback


# callback for indicators
@app.callback([Output("main-content", "children")], [
    Input("indicators", "n_clicks"),  # Define the input components for the callback
    Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date')
], [State("dropdown_tickers", "value")])  # Define the state component for the callback
def indicators(n, start_date, end_date, val):
    if n == None:  # If the "indicators" button has not been clicked
        return [""]  # Return an empty list for the children of "main-content"
    if val == None:  # If no stock ticker has been selected
        return [""]  # Return an empty list for the children of "main-content"

    if start_date == None:  # If a start date has not been selected
        df_more = yf.download(val)  # Download data for the selected stock without specifying a date range
    else:
        df_more = yf.download(val, str(start_date), str(end_date))  # Download data for the selected stock within the specified date range

    df_more.reset_index(inplace=True)  # Reset the index of the DataFrame
    fig = get_more(df_more)  # Generate the figure for additional indicators visualization
    return [dcc.Graph(figure=fig)]  # Return the figure wrapped in a dcc.Graph component for the callback


# callback for forecast
@app.callback([Output("forecast-content", "children")],
              [Input("forecast", "n_clicks")],
              [State("n_days", "value"),
               State("dropdown_tickers", "value")])
def forecast(n, n_days, val):
    if n == None:  # If the "forecast" button has not been clicked
        return [""]  # Return an empty list for the children of "forecast-content"
    if val == None:  # If no stock ticker has been selected
        raise PreventUpdate  # Raise PreventUpdate to prevent updating the callback

    fig = prediction(val, int(n_days) + 1)  # Generate the figure for stock price forecast
    return [dcc.Graph(figure=fig)]  # Return the figure wrapped in a dcc.Graph component for the callback


if __name__ == '__main__':
    http_server = WSGIServer(('', 5000), app)  # Start the HTTP server with WSGI
    http_server.serve_forever()  # Serve the HTTP server indefinitely
