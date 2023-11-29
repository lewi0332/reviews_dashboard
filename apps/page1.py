"""


Author: Derrick Lewis
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from dash import dcc, html
from dash.dependencies import Input, Output
from collections import Counter
from io import BytesIO
from wordcloud import WordCloud
import base64
from plotly_theme_light import plotly_light
from main import app
from apps.tables import defaultColDef

defaultColDef['floatingFilter']=False

pio.templates["plotly_light"] = plotly_light
pio.templates.default = "plotly_light"

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

df_topics = pd.read_parquet(
    'gs://dashapp_project_assests/topics_df.parquet',
)
df_topics.reset_index(inplace=True)

#Top words for positive and negative reviews
pos_words = df[df['item_rating']==1]['tokenized'].to_list()
word_counts_pos = Counter([item for sublist in pos_words for item in sublist])
word_counts_pos = pd.DataFrame(word_counts_pos.most_common(10)).rename(columns={0:'word', 1:'count'})

neg_words = df[df['item_rating']==0]['tokenized'].to_list()
word_counts_neg = Counter([item for sublist in neg_words for item in sublist])
word_counts_neg = pd.DataFrame(word_counts_neg.most_common(10)).rename(columns={0:'word', 1:'count'})


df_month = df.groupby(['vendor_id', 'month_for_plot']).agg({'item_rating': ('sum', 'count', 'mean')})
df_month.columns = ['positive_ratings', 'total_reviews', 'avg_rating']
df_month.reset_index(inplace=True)
df_month = df_month[df_month['total_reviews']>=3]
df_month = df_month.pivot(index='vendor_id', columns='month_for_plot', values='avg_rating').fillna(-100)
df_month['change'] = df_month['2023-09-01'] - df_month['2023-07-01']

df_month = df_month[(df_month['change']>=-1) & (df_month['change']<=1)]

winners = df_month[['change']].sort_values('change', ascending=False).head(10).reset_index().rename(columns={'vendor_id':'Vendor ID', 'change':'Change in Rating'})  
losers = df_month[['change']].sort_values('change', ascending=True).head(10).reset_index().rename(columns={'vendor_id':'Vendor ID', 'change':'Change in Rating'})

change_cols = [
    {"headerName": "Vendor ID", "field": "Vendor ID"},
    {
        "headerName": "Change in Rating",
        "field": "Change in Rating",
        "type": "numericColumn",
        "valueFormatter": {"function": "d3.format(',.1%')(params.value)"},
    }
]
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
            name=f'Average Rating',
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


def plot_topic_distribution(topic_counts)->go.Figure():
    topic_counts = topic_counts.value_counts()
    fig = go.Figure(
            go.Bar(
                x=topic_counts.index,
                y=topic_counts.values,
            )
        )
    fig.update_layout(
            title="Topic Distribution",
            xaxis=dict(title="Topic"),
            yaxis=dict(title="Count")
        )
    return fig

def plot_wordcloud(data:pd.Series) -> BytesIO:
    freq = Counter([item for sublist in data.to_list() for item in sublist])
    wc = WordCloud(
        background_color='white',
        width=350,
        height=125
    )
    wc.fit_words(freq)
    return wc.to_image()

def make_word_cloud_image(dff):
    img = BytesIO()
    plot_wordcloud(data=dff.tokenized).save(img, format='PNG')
    return 'data:image/png;base64,{}'.format(base64.b64encode(img.getvalue()).decode())


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

# --------------------------------------------------------------------
# Create app layout
# ---------------------------------------------------------------------

layout = dbc.Container([
    dbc.Row([
        dbc.Col(
            [
                dcc.Markdown(id='intro',
                children = """
                ---
                # Analysis of Consumer Reviews
                ---

                **TL;DR Summary**
                - Positive reviews are in decline in recent 3 weeks.
                - Common complaints are cold foods, dry foods, and the chicken.
                - The best reviewed vendors are `9150`, `10251`, and `9910`.
                - The worst reviewed vendors are `9687`, `10340`, and `9075`.
                """,
                className='md')
            ])
    ]),
    dbc.Row(
        dbc.Col(
                dcc.Markdown(
                children = """
                ---
                ### Purpose

                This analysis is to explore the results of consumer reviews with the intention of finding insights
                and trends that can increase customer satisfaction and vendor success.

                ### Data

                A sample of ~5k consumer reviews representing ~350 vendors from July to October 2023.

                Each review has a simple positive/negative boolean rating of 0 or 1 and a comment from 
                the consumer.

                ### Methodology

                The analysis was conducted in several steps:

                - **Data Preperation**: The dataset was explored to understand then clean 
                any missing or inconsistent data. This included checking for any reviews without 
                ratings or comments, and removing or imputing these as necessary.

                - **Sentiment Analysis**: Each consumer comment was analyzed using a sentiment 
                analysis algorithm to determine the sentiment score.

                - **Aggregation**: The reviews were then aggregated by vendor to calculate the 
                total number of reviews, the average rating, and the sentiment score for each vendor.

                - **Trend Analysis**: The reviews were analyzed over time to identify any trends 
                or patterns in consumer sentiment. This included looking at changes in the average 
                rating and sentiment score over time.
                """,
                
                className='md')
            ),
    ),
    dbc.Row([
        dbc.Col(
            [
            dcc.Markdown(
                children = """
                ---
                ### Positive Reviews by Week
                
                The chart below shows the ratio of positive reviews to total reviews by week.

                We can see that the ratio of positive reviews has been declining in recent weeks.
                When compared to the first month of data (July), the ratio of positive reviews has
                declined by over 3%.
                """,
                className='md'),
            html.Br(),
            dcc.Graph(id='graph-analysis0',
                      figure=plot_weekly_rating(df, 'item_rating')
                      ),
            dcc.Markdown(
                children = """
                ---
                Follow up analysis should be conducted to determine the cause of this decline.
                """,
                className='md'),
            ]
        )
    ]),
    html.Br(),
    dbc.Row(
        dbc.Col(
            dcc.Markdown(
                children = """
                ---
                ### Common Complaints and Sentiment Analysis
                
                Given the nature of this project, the expected effort ('A couple hours...') and the data available, I have taken three basic approaches to
                identifying common complaints. These approaches are samples and should be refined with 
                more time and data.
                
                **Simple Frequency** The first is a simple look at the most common words in the consumer comments
                based on the self-reported sentiment.

                **Topic Modeling** The second approach is a more complex topic modeling approach. This approach
                uses a Latent Dirichlet Allocation (LDA) model to identify topics in the consumer comments.

                **Sentiment Analysis** The sentiment analysis was conducted using the SpacyTextBlob library. This library
                uses a pretrained model to assign a sentiment score to each comment.
                
                ---
                ### Simple Frequency

                The table below shows the most common words in the consumer comments for positive and negative reviews.
                The word counts are based on the self-reported sentiment of the consumer. The word counts are based on
                the tokenized words in the comments. The tokenized words are the words in the comments after removing
                stop words and non-alpha characters.

                While the simplist method of identifying common complaints, this approach does provide some insight into
                some of the common complaints. For example, the most common words in the negative reviews are 'cold', 'dry',
                and 'chicken'. This suggests that there might be a very specific issue with a vendor.

                This should be followed up with a more detailed analysis of the comments to identify the specific 
                complaints by vendor and perhaps even by week to correlate to other issues.

                This can be done on the subsequent Dashboard page. 
                """,
                className='md'),
        )
    ),
    dbc.Row([
        dbc.Col(width=1),
        dbc.Col([
            dcc.Markdown(
                children = """
                ---
                ##### Frequent words in positive reviews
                """,
                className='md'),
            html.Br(),
            dag.AgGrid(
                id="datatable-pos_words",
                rowData=word_counts_pos.to_dict('records'),
                className="ag-theme-material",
                columnDefs=[{"headerName": x, "field": x, "sortable": True} for x in word_counts_pos.columns],
                columnSize="responsiveSizeToFit",
                defaultColDef=defaultColDef,
                dashGridOptions={"undoRedoCellEditing": True,
                "cellSelection": "single",
                "rowSelection": "single"},
                ),
            html.Br(),
            html.Img(id='graph-analysis2',
                     src=plot_wordcloud(df[df['item_rating']==1]['tokenized'])
                        ),
        ],
        width=5),
        dbc.Col([
            dcc.Markdown(
                children = """
                ---
                ##### Frequent words in negative reviews
                """,
                className='md'),
            html.Br(),
            dag.AgGrid(
                id="datatable-pos_words",
                rowData=word_counts_neg.to_dict('records'),
                className="ag-theme-material",
                columnDefs=[{"headerName": x, "field": x, "sortable": True} for x in word_counts_neg.columns],
                columnSize="responsiveSizeToFit",
                defaultColDef=defaultColDef,
                dashGridOptions={"undoRedoCellEditing": True,
                "cellSelection": "single",
                "rowSelection": "single"},
                ),
            html.Br(),
            html.Img(id='graph-analysis3',
                     src=plot_wordcloud(df[df['item_rating']==0]['tokenized'])
                        ),
        ],
        width=5),

    ]),
    dbc.Row([
        dbc.Col(
            [
            dcc.Markdown(
                children = """
                ---
                ### Topic Modeling

                The topic modeling approach is a exploratory approach to identifying common review topics.
                The LDA model was trained on the consumer comments and the top 10 words for each topic are shown below.
                
                With more time and data, this approach could be used to identify common topics and complaints 
                and should be tracked over time to identify trends as well as the impact of any actions taken.

                Vendors could use this information to identify common complaints and take action to address them.

                """,
                className='md'),
            html.Br(),
            dag.AgGrid(
                rowData=df_topics.to_dict('records'),
                className="ag-theme-material topic-ag-grid",
                columnDefs=[{"headerName": x, "field": x, "sortable": True} for x in df_topics.columns],
                columnSize="responsiveSizeToFit",
                defaultColDef=defaultColDef,
                dashGridOptions={"undoRedoCellEditing": True,
                "cellSelection": "single",
                "rowSelection": "single"},
                style={'height': '300px', 'width': '100%'},
                ),
            html.Br(),
            dcc.Graph(figure=plot_topic_distribution(df['topics'])
            ),
            ]
        )
    ]),
    dbc.Row([
        dbc.Col(
            [
            dcc.Markdown(
                children = """
                ---
                ### Sentiment Analysis

                Each comment was analyzed using a modeling approach to assign a sentiment score to each comment.
                This effort is interesting in that we can see that not all self-reported positive reviews have positive
                comments. The sentiment score is a float between -1 and 1 where -1 is the most negative and 1 is 
                the most positive.

                In some cases, this could a misunderstanding of the rating system. Or prehaps these examples could be users
                who would like to share feedback but are concerned about how their review might effect the vendor's business.

                Overall the sentiment scores are positive, with a mean of 0.14. This suggests that the consumers are generally
                satisfied with the vendors, but there is much room for improvement.

                However, the sentiment score has been declining in recent weeks. This is consistent with the decline in the
                ratio of positive reviews. This suggests that the consumers are becoming less satisfied with the vendors. This change
                over time should be monitored by vendor to identify any specific issues.

                The sentiment score's spike in volume in the `0` bin suggests that there are many reviews that are 
                not able to be analyzed. This is very likely due to short one word comments that are not able to be identified. 
                """,
                className='md'),
            html.Br(),
            dcc.Graph(figure=plot_sentiment(df)),
            html.Br(),
            dcc.Graph(figure=plot_weekly_rating(df, 'sentiment'))
            ]
            ),
    ]),
    dbc.Row([
        dbc.Col(
            dcc.Markdown(
                children = """
                ---
                ### Movers and Shakers

                (Vendor Analysis)

                Given the decline in the ratio of positive reviews and the sentiment score, it would be interesting to
                identify the vendors that have driven that change.

                The table below shows the top 10 vendors by change in their average rating from July to Sept 2023.
                and the bottom 10 vendors by average rating.
                """
            ),
            ),
    ]),
    dbc.Row([
        dbc.Col(width=1),
        dbc.Col([
            dcc.Markdown(
                children = """
                ---
                ##### Getting Better
                """,
                className='md'),
            html.Br(),
            dag.AgGrid(
                rowData=winners.to_dict('records'),
                className="ag-theme-material",
                columnDefs=change_cols,
                columnSize="responsiveSizeToFit",
                defaultColDef=defaultColDef,
                dashGridOptions={"undoRedoCellEditing": True,
                "cellSelection": "single",
                "rowSelection": "single"},
                style={'height': '300px', 'width': '100%'},
                ),
            ],
            width=5
        ),
        dbc.Col([
            dcc.Markdown(
                children = """
                ---
                ##### Having Trouble
                """,
                className='md'),
            html.Br(),
            dag.AgGrid(
                rowData=losers.to_dict('records'),
                className="ag-theme-material",
                columnDefs=change_cols,
                columnSize="responsiveSizeToFit",
                defaultColDef=defaultColDef,
                dashGridOptions={"undoRedoCellEditing": True,
                "cellSelection": "single",
                "rowSelection": "single"},
                style={'height': '300px', 'width': '100%'},
                ),
            ], width=5
        ),
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Markdown(
                children = """
                ---
                ### Conclusion

                The analysis of the consumer reviews has identified some interesting insights and trends.

                - The ratio of positive reviews has been declining in recent weeks.
                - The most common complaints are cold foods, dry foods, and the chicken.
                - The best reviewed vendors are `9150`, `10251`, and `9910`.
                - The worst reviewed vendors are `9687`, `10340`, and `9075`.
                - The sentiment score has been declining in recent weeks.

                The decline in the ratio of positive reviews and the sentiment score suggests that the consumers are becoming
                less satisfied with the vendors. This should be monitored by vendor to identify any specific issues.

                The most common complaints should be followed up with a more detailed analysis of the comments to identify the 
                specific complaints by vendor and perhaps even by week to correlate to other issues.

                This can be done on the subsequent Dashboard page. 
                """,
                className='md'),
        ]),
    ]),
])

# ---------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------
