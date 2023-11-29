'''
EDA - Exploratory Data Analysis of the Consumer Review Dataset

author: @derricklewis

'''
import pandas as pd
import spacy
import plotly.graph_objects as go
from gensim import corpora, models
from gensim.utils import simple_preprocess
from spacytextblob.spacytextblob import SpacyTextBlob
from gensim.parsing.preprocessing import STOPWORDS

# Run this line once to download the spaCy model
# spacy.cli.download('en_core_web_sm')

stopwords = STOPWORDS.union(['order', 'food', 'get'])

df = pd.read_csv(
    'gs://dashapp_project_assests/ds_challenge_dataset_202353.csv',
    parse_dates=['order_date'],
    date_format='%m/%d/%y',
    dtype={
        'order_id': 'str',
        'vendor_id': 'str',
        'item_id': 'str',
        'item_rating': 'int',
        'consumer_comment':'str',
    }
)

df['consumer_comment'] = df['consumer_comment'].astype(str)
df['consumer_comment'] = df['consumer_comment'].str.lower()
df['week'] = df.order_date.dt.to_period('W')
df['week_for_plot'] = df['week'].dt.start_time
df['month'] = df.order_date.dt.to_period('M')
df['month_for_plot'] = df['month'].dt.start_time


# Preprocess the text data
df['tokenized'] = df['consumer_comment'].map(
    lambda doc: [word for word in simple_preprocess(doc) if word not in stopwords]
    )
df['tokenized'] = df['tokenized'].apply(lambda x: [item for item in x if item.isalpha()])

# Create a dictionary representation of the documents
dictionary = corpora.Dictionary(df['tokenized'])

# Convert document into the bag-of-words (BoW) format
bow_corpus = [dictionary.doc2bow(doc) for doc in df['tokenized']]

# Train the LDA model
lda_model = models.LdaModel(bow_corpus, num_topics=10, id2word=dictionary, passes=2)

# Get the topic distribution for each document
topics = [max(lda_model.get_document_topics(bow), key=lambda x: x[1])[0] for bow in bow_corpus]

df['topics'] = topics

# Print the topics
for idx, topic in lda_model.print_topics(-1):
    print('Topic: {} \nWords: {}'.format(idx, topic))

cols = ['word_0', 'word_1', 'word_2', 'word_3', 'word_4', 'word_5', 'word_6', 'word_7', 'word_8', 'word_9']
topics_df = pd.DataFrame(columns=cols)
# Loop over the topics
for topic in lda_model.print_topics(-1):
    # Split the string into word-score pairs
    word_score_pairs = topic[1].split(' + ')
    
    words = []
    # Loop over the word-score pairs
    for pair in word_score_pairs:
        # Split the pair into word and score
        score, word = pair.split('*')
        
        # Remove the quotes around the word
        word = word.strip('"')
        
        # Add the topic ID, word, and score to the list
        words.append(word)
    temp = pd.DataFrame(index=cols, columns=[topic[0]], data=words).T
    
    topics_df = pd.concat([topics_df, temp])
# rename index
topics_df.index.name = 'topic_id'


# ---------------------------------------------------------------------
# Sentiment Analysis
# ---------------------------------------------------------------------

# Load spaCy model
nlp = spacy.load('en_core_web_sm')

# Add TextBlob as a pipeline component
nlp.add_pipe('spacytextblob')

# Perform sentiment analysis
df['sentiment'] = df['consumer_comment'].apply(lambda comment: nlp(comment)._.polarity)

# ---------------------------------------------------------------------
# Store the dataframes as parquet files
# ---------------------------------------------------------------------

df.to_parquet('gs://dashapp_project_assests/df.parquet')
topics_df.to_parquet('gs://dashapp_project_assests/topics_df.parquet')


