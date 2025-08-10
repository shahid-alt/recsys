import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

export const fetchMovies = (page = 1) => api.get(`/movies/?page=${page}`);
export const searchMovies = (query, { page = 1, year, language, genre, status } = {}) => {
  const params = { query, page };
  if (year) params.year = year;
  if (language) params.language = language;
  if (genre) params.genre = genre;
  if (status) params.status = status;
  return api.get('/movies/search/', { params });
};
export const fetchMovieDetails = (id) => api.get(`/movies/${id}/`);
export const fetchMovieCredits = (id) => api.get(`/movies/${id}/credits/`);
export const fetchGenres = () => api.get('/genres/');
export const fetchMoviesByGenre = (genre, page = 1) => api.get(`/genres/${genre}/?page=${page}`);
export const fetchPeople = (page = 1) => api.get(`/people/?page=${page}`);
export const fetchPersonDetails = (id) => api.get(`/people/${id}/`);