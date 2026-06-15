import os
import kagglehub
from download_file import download_file

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    tmdb_output_dir = os.path.abspath(os.path.join(base_dir, "..", "..", "datasets", "tmdb_movie_metadata"))
    grouplens_ratings_dir = os.path.abspath(os.path.join(base_dir, "..", "..", "datasets", "grouplens_ratings"))
    imdb_titles_dir = os.path.abspath(os.path.join(base_dir, "..", "..", "datasets", "imdb_titles"))

    os.makedirs(tmdb_output_dir, exist_ok=True)
    os.makedirs(grouplens_ratings_dir, exist_ok=True)
    os.makedirs(imdb_titles_dir, exist_ok=True)

    title_basics_file_path = os.path.join(imdb_titles_dir, "title.basics.tsv.gz")

    # ------------------------------------------------------------------
    # DOWNLOAD 1: TMDB Movie Metadata
    # ------------------------------------------------------------------
    print("Downloading TMDB Movie Metadata...")
    path_tmdb = kagglehub.dataset_download(handle="tmdb/tmdb-movie-metadata", output_dir=tmdb_output_dir)
    print("TMDB dataset path:", path_tmdb)

    # ------------------------------------------------------------------
    # DOWNLOAD 2: GroupLens Ratings
    # ------------------------------------------------------------------
    print("\nDownloading GroupLens Ratings...")
    url_grouplens = 'https://files.grouplens.org/datasets/movielens/ml-32m.zip'
    download_file(url_grouplens, os.path.join(grouplens_ratings_dir, "ml-32m.zip"))
