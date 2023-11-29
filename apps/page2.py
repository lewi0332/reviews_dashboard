"""

Author: Derrick Lewis
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import dash_bootstrap_components as dbc
from dash import dcc, html
import dash_ag_grid as dag
from dash.dependencies import Input, Output
from dotenv import load_dotenv
from apps.tables import columnDefs, defaultColDef

from plotly_theme_light import plotly_light

from main import app

from collections import Counter
from io import BytesIO
from wordcloud import WordCloud
import base64

pio.templates["plotly_light"] = plotly_light
pio.templates.default = "plotly_light"
load_dotenv()

# Table settings
CELL_PADDING = 5
DATA_PADDING = 5
TABLE_PADDING = 1
FONTSIZE = 12

# ---------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------

df = pd.read_parquet(
    'gs://dashapp_project_assests/df.parquet',
)

# Get the mean rating for last week
last_week = df.week.max()
df_last_week = df[df['week'] == last_week]
mean_last_week = df_last_week.item_rating.mean()

# Get the mean rating for the week before
week_before = df.week.unique()[-2]
df_week_before = df[df['week'] == week_before]
mean_week_before = df_week_before.item_rating.mean()

# Calculate WoW change
delta_WoW = mean_last_week - mean_week_before

# Calculate difference from mean
delta_mean = mean_last_week - df.item_rating.mean()


# ---------------------------------------------------------------------
# Python functions
# ---------------------------------------------------------------------

def plot_weekly_rating(dff:pd.DataFrame, feature:str) -> go.Figure:   
    df_week = dff.groupby('week_for_plot').agg({feature: ('sum', 'count', 'mean')})
    df_week.columns = ['positive_ratings', 'total_reviews', 'avg_rating']
    overal_ave = df_week.avg_rating.mean()
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df_week.index,
            y=df_week['avg_rating'],
            name='Average Rating',
            hovertemplate=
            '<i>Week Starting</i>: %{x}<br>' +
            '<b>Average Rating</b>: %{y:.2%}<br><extra></extra>',
        )
    )
    # add a horizontal line for the overall mean
    fig.add_shape(
        type='line',
        x0=df_week.index[0],
        y0=overal_ave,
        x1=df_week.index[-1],
        y1=overal_ave,
        line=dict(
            color='red',
            width=2,
            dash='dash'
        )
    )
    fig.add_annotation(
        x=df_week.index[-1],
        y=overal_ave,
        text=f"Overall Average Rating: {overal_ave:.2%}"
    )
    fig.update_yaxes(tickformat='.0%')
    fig.update_layout(
        title="Weekly Ratings",
        xaxis_title='Week',
        yaxis_title='Average Rating'
    )
    return fig

def plot_wordcloud(data:pd.Series) -> BytesIO:
    freq = Counter([item for sublist in data.to_list() for item in sublist])
    wc = WordCloud(
        background_color='white',
        width=1000,
        height=500
    )
    wc.fit_words(freq)
    return wc.to_image()

def make_word_cloud_image(dff):
    img = BytesIO()
    plot_wordcloud(data=dff.tokenized).save(img, format='PNG')
    return 'data:image/png;base64,{}'.format(base64.b64encode(img.getvalue()).decode())

def make_items_plot(dff, vendor_id=None):
    if vendor_id:
        dff = dff[dff['vendor_id'] == vendor_id]
    df_item = dff.groupby('item_id').agg({'item_rating': ('sum', 'count', 'mean')}).sort_values(('item_rating', 'count'), ascending=False).head(20)
    # Scale marker size based on number of ratings
    marker_size = (df_item[('item_rating', 'count')] / df_item[('item_rating', 'count')].max()) * 40 + 10

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_item[('item_rating', 'sum')],
            y=df_item[('item_rating', 'mean')],
            name='Average Rating',
            mode='markers',
            text=df_item.index,
            hovertemplate=
            '<i>Total Ratings</i>: %{x}<br>' +
            '<b>Average Rating</b>: %{y:.2%}<br>' +
            '<b>Food Item</b>: %{text}<extra></extra>',
            marker=dict(
                size=marker_size,
                showscale=False
            ),
        )
    )
    fig.update_layout(
        title='Ratings for the 20 Most Reviewed Items',
        xaxis_title='Total Ratings',
        yaxis_title='Average Rating'
    )
    fig.update_yaxes(tickformat='.0%')
    return fig

def plot_sentiment(dff):
    sent_mean = dff['sentiment'].mean()
    fig = go.Figure(
            go.Histogram(
                x=dff['sentiment'],
                name='Sentiment'
                )
        )
    fig.add_shape(
        type='line',
        x0=sent_mean,
        y0=0,
        x1=sent_mean,
        y1=dff['sentiment'].value_counts().max(),
        line=dict(
            color='red',
            width=2,
            dash='dash'
        )
    )
    fig.add_annotation(
        x=sent_mean,
        y=dff['sentiment'].value_counts().max(),
        text=f'Mean Sentiment: {sent_mean:.2f}'
    )
    fig.update_layout(
        title="Sentiment Distribution<br><sub>Greater than 0 is positive, less than 0 is negative</sub>",
        xaxis=dict(title="Sentiment"),
        yaxis=dict(title="Count")
    )
    return fig

# ---------------------------------------------------------------------
# Create app layout
# ---------------------------------------------------------------------

layout = dbc.Container([
    dbc.Row([
        dbc.Col(
            [
                dcc.Markdown(id='intro',
                children = """
                ---
                # Dashboard
                """,
                className='md')
            ]),
        dbc.Col(
           [
                dcc.Markdown(id='intro',
                children = """
                ---
                Choose a Vendor ID to see the ratings for that vendor.
                """,
                className='md',
                ),
                dcc.Dropdown(
                    id='vendor_id',
                    placeholder='All Vendors',
                    options=[{'label': i, 'value': i} for i in df.vendor_id.value_counts().index],
                    value=None
                ),
                html.Br(),
                # add reset button to see all vendors
                dbc.Button('Reset', 
                           id='reset',
                           style={
                                    'background-color': 'rgba(0, 203, 166, 0.7)',
                                    'border': 'none',
                                    'color': 'white',
                                    'padding': '10px',
                                    'margin-top': '5px',
                                    'margin-bottom': '10px',
                                    'text-align': 'center',
                                    'text-decoration': 'none',
                                    'font-size': '12px',
                                    'border-radius': '26px'
                                }
                )
           ]),
        
    ]),
    html.Br(),
    dbc.Row(
            dbc.Col([
                dcc.Markdown(
                    children = """
                    ---
                    """,
                    className='md'),
                html.H2(f'Current Rating - Week of {df["week_for_plot"].max().strftime("%Y-%m-%d")}: ',
                        style={
                            'font-weight': 'light',
                            'color': 'grey',
                            'text-align': 'center',
                            'font-size': 24,
                        }
                ),
                html.H1(id='mean_agg_rating',
                        children=f"{mean_last_week:.1%}",
                        style={
                            'font-weight': 'light',
                            'font-size': 36,
                            'padding': 0,
                            'textAlign': 'center',
                            'margin-bottom': 0
                        }
                ), 
            
            ],
                align="center", width=6
            ),
        justify='center', align='center', style={'padding-top': 0}
    ),
    html.Br(),
    dbc.Row([
            dbc.Col(width=1),
            dbc.Col(
                [
                html.H2('Change WoW: ',
                        style={
                            'font-weight': 'light',
                            'color': 'grey',
                            'font-size': 24,
                            'textAlign': 'center'
                        }),
                html.H1(id='delta_WoW',
                        children=f"{delta_WoW:.2%}",
                        style={
                            'font-weight': 'light',
                            'font-size': 36,
                            'padding': 0,
                            'textAlign': 'center',
                            'margin-bottom': 0
                        }),
                ],
                align="center", width=5,
            ),
            dbc.Col([
                html.H2('Difference from Mean: ',
                        style={
                            'font-weight': 'light',
                            'color': 'grey',
                            'font-size': 24,
                            'text-align': 'center'
                        }),
                html.H1(id='delta_mean',
                        children=f"{delta_mean:.2%}",
                        style={
                            'font-weight': 'light',
                            'font-size': 36,
                            'padding': 0,
                            'textAlign': 'center',
                            'margin-bottom': 0
                        })
            ], 
            align="center", width=5
            )
    ]),
    html.Br(),
    dbc.Row(
        dbc.Col([
            dcc.Markdown(
                children = """
                ---
                """,
                className='md'),
            dcc.Graph(id='graph-main1',
                      figure=plot_weekly_rating(df, 'item_rating')
            )
        ])
    ),
    dbc.Row(
        dbc.Col(
            dcc.Markdown(
                children = """
                ---
                ### Modeled Comment Sentiment Analysis
                """,
                className='md')
        ),
    ),
    dbc.Row([
        dbc.Col(width=1),
        dbc.Col(
            dcc.Graph(id='graph-main4',
                      figure=plot_sentiment(df)
            ),    
            width=5
        ),
        dbc.Col(
            dcc.Graph(id='graph-main5',
                      figure=plot_weekly_rating(df, 'sentiment')
            ),
            width=5
        ),
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Markdown(
                children = """
                ---
                ### Most Reviewed Items
                """,
                className='md'),
            html.Br(),
            dcc.Graph(id='graph-main3',
                      figure=make_items_plot(df))
        ])
    ]),
    html.Br(),
    dbc.Row(
        dbc.Col([
            dcc.Markdown(
                children = """
                ---
                ### Comments from Consumers
                """,
                className='md'),
            html.Br(),
            dcc.RadioItems(
                id='radio',
                options=[
                    {'label': 'All', 'value': 'all'},
                    {'label': 'Positive', 'value': 'pos'},
                    {'label': 'Negative', 'value': 'neg'}
                ],
                value='all',
                inline=True,
                labelStyle={'display': 'inline-block', 'margin-right': '20px'}
            ),
            html.Br(),
            html.Img(id='graph-main2',
                    src=make_word_cloud_image(df))
        ]),
        
    ),
    dbc.Row([
        dbc.Col(
            [
            html.Br()
            ]
        ),
        dbc.Col(width=1),
        dbc.Col(
            [
            html.Br()
            ]
        )
    ]),

    dbc.Row([
        dbc.Col(
            [
            html.Br()
            ]
        ),
        dbc.Col(width=1),
        dbc.Col(
            [
            html.Br()
            ]
        )
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Markdown(
                children = """
                ---
                ### Sample Consumer Reviews
                """,
                className='md'),
            html.Br(),
            dag.AgGrid(
                id="datatable-time",
                rowData=df[['order_date', 'item_rating', 'consumer_comment']].to_dict("records"),
                className="ag-theme-material",
                columnDefs=columnDefs,
                columnSize="responsiveSizeToFit",
                defaultColDef=defaultColDef,
                dashGridOptions={"undoRedoCellEditing": True,
                "cellSelection": "single",
                "rowSelection": "single"},
                # csvExportParams={"fileName": "top02_arrest_rate.csv", "columnSeparator": ","},
                # style = {'width': '100%', 'color': 'grey'}
                ),
        ])
    ]),
    dbc.Row([
        dbc.Col(
            [
            html.Br()
            ]
        ),
        dbc.Col(width=1),
        dbc.Col(
        
        )
    ]),
    html.Br(),
]
)

# ---------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------

@app.callback([
    Output('graph-main1', 'figure'),
    Output('graph-main5', 'figure'),
    Output('graph-main4', 'figure'),],
    Input('vendor_id', 'value')
)
def update_graph_main1(vendor_id):
    if vendor_id:
        dff = df[df['vendor_id'] == vendor_id]
    else:
        dff = df
    return plot_weekly_rating(dff, 'item_rating'), plot_weekly_rating(dff, 'sentiment'), plot_sentiment(dff)


@app.callback(
    Output('graph-main2', 'src'),
    [Input('vendor_id', 'value'),
    Input('radio', 'value')]
)
def update_graph_main2(vendor_id, review_type):
    if vendor_id:
        dff = df[df['vendor_id'] == vendor_id]
    else:
        dff = df
    if review_type:
        if review_type == 'all':
            dff = dff
        elif review_type == 'pos':
            dff = dff[dff['item_rating'] == 1]
        else:
            dff = dff[dff['item_rating'] == 0]
    return make_word_cloud_image(dff)

@app.callback(
    Output('graph-main3', 'figure'),
    Input('vendor_id', 'value')
)
def update_graph_main3(vendor_id):
    return make_items_plot(df, vendor_id)

@app.callback(
    Output('vendor_id', 'value'),
    Input('reset', 'n_clicks')
)
def reset_vendor_id(n_clicks):
    return None

@app.callback(
    Output('datatable-time', 'rowData'),
    Input('vendor_id', 'value')
)
def update_datatable(vendor_id):
    if vendor_id:
        dff = df[df['vendor_id'] == vendor_id]
    else:
        dff = df
    return dff[['order_date', 'item_id', 'item_rating', 'consumer_comment']].to_dict("records")

@ app.callback([
    Output('mean_agg_rating', 'children'),
    Output('delta_WoW', 'children'),
    Output('delta_mean', 'children'),
    Output('delta_WoW', 'style'),
    Output('delta_mean', 'style')

],
  Input('vendor_id', 'value')
)
def label_annotations(vendor_id):
    if vendor_id:
        dff = df[df['vendor_id'] == vendor_id]
    else:
        dff = df
    last_week = dff.week.max()
    dff_last_week = dff[dff['week'] == last_week]
    mean_last_week = dff_last_week.item_rating.mean()

    # Get the mean rating for the week before
    week_before = dff.week.unique()[-2]
    dff_week_before = dff[dff['week'] == week_before]
    mean_week_before = dff_week_before.item_rating.mean()

    # Calculate WoW change
    delta_WoW = mean_last_week - mean_week_before

    # Calculate difference from mean
    delta_mean = mean_last_week - dff.item_rating.mean()

    if delta_WoW > 0:
        delta_wow_style = {
            'font-weight': 'light',
            'color': 'green',
            'padding': 0,
            'textAlign': 'center',
            'margin-top': 0
        }
    else:
        delta_wow_style = {
            'font-weight': 'light',
            'color': 'red',
            'padding': 0,
            'textAlign': 'center',
            'margin-top': 0
        }
    if delta_mean > 0:
        delta_mean_style = {
            'font-weight': 'light',
            'color': 'green',
            'padding': 0,
            'textAlign': 'center',
            'margin-top': 0
        }
    else:
        delta_mean_style = {
            'font-weight': 'light',
            'color': 'red',
            'padding': 0,
            'textAlign': 'center',
            'margin-top': 0
        }
    return f"{mean_last_week:.1%}", f"{delta_WoW:.2%}", f"{delta_mean:.2%}", delta_wow_style, delta_mean_style