import os
import pandas as pd
import ast

base_path = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(base_path, '../../datasets/tmdb_movie_metadata')
cleaned_dataset_path = os.path.join(base_path, '../../datasets/cleaned_tmdb_dataset')

if not os.path.exists(cleaned_dataset_path):
    print("Creating directory for cleaned dataset...")
    os.makedirs(cleaned_dataset_path)


def parse_json_column(column_data):
    """Parses a string representation of a list of dictionaries."""
    try:
        return ast.literal_eval(column_data)
    except (ValueError, SyntaxError):
        return []

def extract_names(json_list):
    """Extracts 'name' values from a list of dictionaries."""
    return [d['name'] for d in json_list if 'name' in d]

print("Loading datasets...")
movies_df = pd.read_csv(os.path.join(dataset_path, 'tmdb_5000_movies.csv'))
credits_df = pd.read_csv(os.path.join(dataset_path, 'tmdb_5000_credits.csv'))

# Merge datasets on id
df = movies_df.merge(credits_df, left_on='id', right_on='movie_id')

print(f"Merged dataset shape: {df.shape}")

print("Cleaning JSON columns...")
json_columns = ['genres', 'keywords', 'production_companies', 'production_countries', 'cast', 'crew']

for col in json_columns:
    if col in df.columns:
        df[col] = df[col].apply(parse_json_column)
        if col in ['genres', 'keywords']:
            df[col] = df[col].apply(extract_names)

df['cast_names'] = df['cast'].apply(lambda x: [d['name'] for d in x])
df['crew_names'] = df['crew'].apply(lambda x: [d['name'] for d in x])

print("Saving cleaned dataset...")
df.to_csv(os.path.join(cleaned_dataset_path, 'cleaned_tmdb_data.csv'), index=False)
df.head(2)