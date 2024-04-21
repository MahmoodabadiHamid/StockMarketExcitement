import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
from jdatetime import datetime as jdatetime
from jdatetime import time

start_time = time(9, 0)
end_time = time(12, 31) 

# Read data from file
with open("data.txt") as file:
    data_str = file.read()

# Process data
data = []
complete_data = []
for line in data_str.split('\n')[1:]:
    if line:
        try:
            date, time, value = line.split()
            gregorian_date = jdatetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d')
            date_time = f"{gregorian_date} {time}"
            dt_obj = jdatetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')
            
            # Filter rows with times rounded to :00 and :30
            if 8 < dt_obj.hour < 13 and dt_obj.minute % 30 == 0:
                data.append({"Date": date, "Time": dt_obj.strftime("%H:%M"), 'DateTime': dt_obj, 'Value': float(value.replace(',', ''))})
            if start_time <= dt_obj.time() <= end_time:
                #complete_data.append({"Date": date, "Time": dt_obj.strftime("%H:%M"), 'DateTime': dt_obj, 'Value': float(value.replace(',', ''))})
                complete_data.append({"Date": date, "Time": dt_obj.strftime("%H:%M"), 'DateTime': dt_obj, 'Value': float(value.replace(',', ''))})
        except Exception as e:
            continue

# Calculate PercentChange
for i in range(1, len(data)):
    data[i]['PercentChange'] = ((data[i]['Value'] - data[i - 1]['Value']) / data[i - 1]['Value']) * 100

for i in range(1, len(complete_data)):
    complete_data[i]['PercentChange'] = ((complete_data[i]['Value'] - complete_data[i - 1]['Value']) / complete_data[i - 1]['Value']) * 100


df = pd.DataFrame(data)

complete_df = pd.DataFrame(complete_data)
complete_df['Time'] = pd.to_datetime(complete_df['Time']).dt.round('5min').dt.strftime('%H:%M')
#df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce')


# Create a Dash web application
app = dash.Dash(__name__)

# Define the layout of the web application
app.layout = html.Div([
    html.H1("Stock Market Index Excitement"),

    html.Label("Select Date(s):"),
    html.Div([
        dcc.Dropdown(
            id='year-dropdown',
            options=[{'label': item, 'value': item} for item in list(set(i.year for i in df['DateTime'].unique()))],
            multi=True,
            value=["1401"],
            style={'width': '100%'},
        ),
        dcc.Dropdown(
            id='month-dropdown',
            options=[{'label': item, 'value': item} for item in list(set(i.month for i in df['DateTime'].unique()))],
            multi=True,
            value=["1", "2"],
            style={'width': '100%'},
        ),
        dcc.Dropdown(
            id='day-dropdown',
            options=[{'label': item, 'value': item} for item in list(set(i.day for i in df['DateTime'].unique()))],
            multi=True,
            value=["13", "14", "15", "16", "17"],
            style={'width': '100%'},
        ),
    ], style={'display': 'flex', 'flexDirection': 'row', 'width': '100%'}),
    
   dcc.Checklist(
        id='percent-change-checkbox',
        options=[
            {'label': 'Percent Changes based on Yesterday value', 'value': 'show-percent-change'}
        ],
        value=[],
    ),
    dcc.Checklist(
        id='show_complete_data',
        options=[
            {'label': 'Show complete data', 'value': 'partial_data'}
        ],
        value=[],
    ),
    html.Label("Select Time:"),
    dcc.Dropdown(
        id='time-dropdown',
        options=[{'label': f"{h:02d}:{m:02d}", 'value': f"{h:02d}:{m:02d}"} for h in range(9, 13) for m in range(0, 60, 30)],
        placeholder="Select time",
        multi=False,
        style={'width': '50%'}
    ),

    html.Label("Select Percent Change:"),
    dcc.Dropdown(
        id='percent-change-dropdown',
        options=[{'label': str(i), 'value': str(i)} for i in range(5, -6, -1)],
        placeholder="Select percent change",
        multi=False,
        style={'width': '50%'}
    ),

    dcc.Graph(id='excitement-chart'),
])

@app.callback(
    Output('excitement-chart', 'figure'),
    [Input('year-dropdown', 'value'),
     Input('month-dropdown', 'value'),
     Input('day-dropdown', 'value'),
     Input('time-dropdown', 'value'),
     Input('percent-change-checkbox', 'value'),
     Input('percent-change-dropdown', 'value'),
     Input('show_complete_data', 'value')]
)
def update_chart(selected_years, selected_months, selected_days, selected_time, show_percent_change, selected_percent_change, show_complete_data):

    if show_complete_data:
        filtered_df = complete_df
    else:
        filtered_df = df

    # Filter by selected years
    if selected_years:
        filtered_df = filtered_df[filtered_df['DateTime'].apply(lambda x: x.year).isin([int(i) for i in selected_years])]

    # Filter by selected months
    if selected_months:
        filtered_df = filtered_df[filtered_df['DateTime'].apply(lambda x: x.month).isin([int(i) for i in selected_months if i != "All"])]

    # Filter by selected days
    if selected_days:
        filtered_df = filtered_df[filtered_df['DateTime'].apply(lambda x: x.day).isin([int(i) for i in selected_days])]

    title = f"Stock Market Index Excitement"
    if show_complete_data:
        #show_percent_change = False
        if show_percent_change:
            # Calculate Percent Change from the beginning of the day at 09:00
            #filtered_df['PercentChange'] = ((filtered_df['Value'] - filtered_df.loc[filtered_df['Time'] == '09:00', 'Value'].iloc[0]) / filtered_df.loc[filtered_df['Time'] == '09:00', 'Value'].iloc[0]) * 100
            filtered_df['PercentChange'] = ((filtered_df['Value'] - filtered_df.groupby('Date')['Value'].transform('first')) / filtered_df.groupby('Date')['Value'].transform('first')) * 100
            y_axis_label = 'Percent Change from Beginning'
        else:
            # Calculate Percent Change from the previous data point with 09:00 being treated as zero
                filtered_df['PercentChange'] = ((filtered_df['Value'] - filtered_df['Value'].shift(1)) / filtered_df['Value'].shift(1)) * 100
                # Set the percent change for the first data point at 09:00 to be zero
                filtered_df.loc[filtered_df['Time'] == '09:00', 'PercentChange'] = 0
                y_axis_label = 'Percent Change'
    else:
        #show_percent_change = False
        if show_percent_change:
            # Calculate Percent Change from the beginning of the day at 09:00
            filtered_df['PercentChange'] = ((filtered_df['Value'] - filtered_df.groupby('Date')['Value'].transform('first')) / filtered_df.groupby('Date')['Value'].transform('first')) * 100
            y_axis_label = 'Percent Change from Beginning'
        else:
            # Calculate Percent Change from the previous data point with 09:00 being treated as zero
                filtered_df['PercentChange'] = ((filtered_df['Value'] - filtered_df['Value'].shift(1)) / filtered_df['Value'].shift(1)) * 100
                # Set the percent change for the first data point at 09:00 to be zero
                filtered_df.loc[filtered_df['Time'] == '09:00', 'PercentChange'] = 0
                y_axis_label = 'Percent Change'
    if selected_time != None and selected_percent_change != None:
        selected_dates = filtered_df[(filtered_df['Time'] == selected_time) & (filtered_df['PercentChange'].round() == int(selected_percent_change))]['Date']
        filtered_df = filtered_df[filtered_df['Date'].isin(selected_dates)] 
    
    hover_data = {'Date': True, 'Time': True, 'PercentChange': True, 'Value': ':,.0f'}
    fig = px.line(filtered_df, x='Time', y='PercentChange', color='Date', title=title, hover_data=hover_data)
    fig.update_xaxes(title_text='Time')
    fig.update_yaxes(title_text=y_axis_label)
    fig.update_layout(height=800)
    
    return fig

# Run the application
if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port="8085")



