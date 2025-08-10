import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { searchMovies, fetchGenres } from '../api/tmdb';
import MovieCard from '../components/MovieCard';
import Pagination from '../components/Pagination';

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [genres, setGenres] = useState([]);
  const [filters, setFilters] = useState({
    query: searchParams.get('query') || '',
    year: searchParams.get('year') || '',
    language: searchParams.get('language') || '',
    genre: searchParams.get('genre') || '',
    status: searchParams.get('status') || ''
  });

  // Fetch genres on component mount
  useEffect(() => {
    const fetchGenreList = async () => {
      try {
        const response = await fetchGenres();
        setGenres(response.data);
      } catch (error) {
        console.error("Error fetching genres:", error);
      }
    };
    fetchGenreList();
  }, []);

  // Search when filters or page change
  useEffect(() => {
    const search = async () => {
      if (!hasActiveFilters()) {
        setMovies([]);
        setTotalPages(1);
        return;
      }
      
      try {
        setLoading(true);
        const response = await searchMovies(filters.query, {
          page: currentPage,
          year: filters.year,
          language: filters.language,
          genre: filters.genre,
          status: filters.status
        });
        setMovies(response.data.results);
        setTotalPages(Math.ceil(response.data.total_count / 20));
      } catch (error) {
        console.error("Search error:", error);
        setMovies([]);
        setTotalPages(1);
      } finally {
        setLoading(false);
      }
    };

    search();
  }, [filters, currentPage]);

  const hasActiveFilters = () => {
    return filters.query || filters.year || filters.language || filters.genre || filters.status;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    updateUrlParams(filters);
    setCurrentPage(1);
  };

  const updateUrlParams = (filters) => {
    const params = {};
    if (filters.query) params.query = filters.query;
    if (filters.year) params.year = filters.year;
    if (filters.language) params.language = filters.language;
    if (filters.genre) params.genre = filters.genre;
    if (filters.status) params.status = filters.status;
    setSearchParams(params);
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  const clearFilters = () => {
    const newFilters = {
      query: '',
      year: '',
      language: '',
      genre: '',
      status: ''
    };
    setFilters(newFilters);
    setSearchParams({});
    setCurrentPage(1);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6 text-white">Search Movies</h1>
      
      <form onSubmit={handleSubmit} className="mb-8">
        <div className="flex flex-col gap-4">
          <div className="flex gap-2">
            <input
              type="text"
              name="query"
              value={filters.query}
              onChange={handleFilterChange}
              placeholder="Search for movies..."
              className="flex-1 p-3 border border-gray-700 bg-gray-800 text-white rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
            />
            <button 
              type="submit"
              className="bg-gradient-to-r from-amber-500 to-amber-600 text-white px-6 py-3 rounded-lg hover:from-amber-600 hover:to-amber-700 transition-all shadow-lg"
            >
              Search
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Release Year</label>
              <input
                type="number"
                name="year"
                value={filters.year}
                onChange={handleFilterChange}
                placeholder="Filter by year"
                min="1900"
                max={new Date().getFullYear() + 5}
                className="w-full p-2 border border-gray-700 bg-gray-800 text-white rounded focus:ring-amber-500 focus:border-amber-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Language</label>
              <input
                type="text"
                name="language"
                value={filters.language}
                onChange={handleFilterChange}
                placeholder="Filter by language (en, fr, etc.)"
                className="w-full p-2 border border-gray-700 bg-gray-800 text-white rounded focus:ring-amber-500 focus:border-amber-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Genre</label>
              <select
                name="genre"
                value={filters.genre}
                onChange={handleFilterChange}
                className="w-full p-2 border border-gray-700 bg-gray-800 text-white rounded focus:ring-amber-500 focus:border-amber-500"
              >
                <option value="">All Genres</option>
                {genres.map(genre => (
                  <option key={genre.id} value={genre.name}>
                    {genre.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Status</label>
              <select
                name="status"
                value={filters.status}
                onChange={handleFilterChange}
                className="w-full p-2 border border-gray-700 bg-gray-800 text-white rounded focus:ring-amber-500 focus:border-amber-500"
              >
                <option value="">All Statuses</option>
                <option value="Released">Released</option>
                <option value="In Production">In Production</option>
                <option value="Post Production">Post Production</option>
                <option value="Planned">Planned</option>
                <option value="Rumored">Rumored</option>
                <option value="Canceled">Canceled</option>
              </select>
            </div>
          </div>
        </div>
      </form>

      {/* Active filters - now with dark theme */}
      {hasActiveFilters() && (
        <div className="mb-6 p-4 bg-gray-800 rounded-lg border border-gray-700 shadow">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-gray-300">Active Filters:</h3>
            <button
              type="button"
              onClick={clearFilters}
              className="text-sm text-amber-400 hover:text-amber-300 transition-colors flex items-center gap-1"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              Clear all
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {filters.query && (
              <span className="bg-gray-700 text-amber-400 px-3 py-1 rounded-full text-sm flex items-center gap-1">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                </svg>
                {filters.query}
              </span>
            )}
            {filters.year && (
              <span className="bg-gray-700 text-gray-300 px-3 py-1 rounded-full text-sm flex items-center gap-1">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                </svg>
                {filters.year}
              </span>
            )}
            {filters.language && (
              <span className="bg-gray-700 text-gray-300 px-3 py-1 rounded-full text-sm flex items-center gap-1">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M7 2a1 1 0 011 1v1h3a1 1 0 110 2H9.578a18.87 18.87 0 01-1.724 4.78c.29.354.596.696.914 1.026a1 1 0 11-1.44 1.389c-.188-.196-.373-.396-.554-.6a19.098 19.098 0 01-3.107 3.567 1 1 0 01-1.334-1.49 17.087 17.087 0 003.13-3.733 18.992 18.992 0 01-1.487-2.494 1 1 0 111.79-.89c.234.47.489.928.764 1.372.417-.934.752-1.913.997-2.927H3a1 1 0 110-2h3V3a1 1 0 011-1zm6 6a1 1 0 01.894.553l2.991 5.982a.869.869 0 01.02.037l.99 1.98a1 1 0 11-1.79.895L15.383 16h-4.764l-.724 1.447a1 1 0 11-1.788-.894l.99-1.98.019-.038 2.99-5.982A1 1 0 0113 8zm-1.382 6h2.764L13 11.236 11.618 14z" clipRule="evenodd" />
                </svg>
                {filters.language}
              </span>
            )}
            {filters.genre && (
              <span className="bg-gray-700 text-gray-300 px-3 py-1 rounded-full text-sm flex items-center gap-1">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" />
                </svg>
                {filters.genre}
              </span>
            )}
            {filters.status && (
              <span className="bg-gray-700 text-gray-300 px-3 py-1 rounded-full text-sm flex items-center gap-1">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                {filters.status}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Results section */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-amber-500"></div>
        </div>
      ) : (
        <>
          {hasActiveFilters() && movies.length === 0 && (
            <div className="text-center p-8 bg-gray-800 rounded-lg border border-gray-700">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="mt-4 text-lg font-medium text-gray-300">No results found</h3>
              <p className="mt-1 text-gray-500">Try adjusting your search filters</p>
            </div>
          )}
          
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
            {movies.map(movie => (
              <MovieCard key={movie.id} movie={movie} />
            ))}
          </div>

          {movies.length > 0 && (
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={setCurrentPage}
            />
          )}
        </>
      )}
    </div>
  );
}