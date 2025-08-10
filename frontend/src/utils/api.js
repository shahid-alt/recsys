import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
});

export const fetchMovies = () => api.get('/movies/');
export const searchMovies = (params) => api.get('/movies/search/', { params });
export const fetchMovieDetails = (id) => api.get(`/movies/${id}/`);
export const fetchPeople = () => api.get('/people/');
export const fetchPersonDetails = (id) => api.get(`/people/${id}/`);
export const fetchGenres = () => api.get('/genres/');
export const fetchMoviesByGenre = (genre) => api.get(`/genres/${genre}/`);