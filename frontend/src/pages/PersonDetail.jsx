import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import MovieCard from '../components/MovieCard';

export default function PersonDetail() {
  const { id } = useParams();
  const [person, setPerson] = useState(null);
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const API_BASE_URL = import.meta.env.VITE_TMDBMIRROR_BACKEND_URL;
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch person details
        const personResponse = await axios.get(`${API_BASE_URL}/people/${id}/`);
        setPerson(personResponse.data);
        
        // Fetch movies they appeared in
        try {
          const moviesResponse = await axios.get(`${API_BASE_URL}/people/${id}/movies/`);
          setMovies(moviesResponse.data.results || []);
        } catch (error) {
          console.error("Error fetching person's movies:", error);
          setMovies([]);
        }
      } catch (error) {
        console.error("Error fetching person details:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  if (loading) return (
    <div className="flex justify-center items-center h-screen">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-amber-500"></div>
    </div>
  );
  
  if (!person) return (
    <div className="text-center p-8 text-gray-300">
      Person not found
    </div>
  );

  return (
    <div className="container mx-auto px-4 py-8">
      <Link 
        to="/people" 
        className="inline-flex items-center gap-2 text-amber-400 hover:text-amber-300 transition-colors mb-6"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
        </svg>
        Back to People
      </Link>

      <div className="bg-gray-800 rounded-xl shadow-xl overflow-hidden">
        <div className="md:flex">
          {/* Person Photo */}
          <div className="md:w-1/3 p-6">
            {person.profile_path ? (
              <img
                src={`https://image.tmdb.org/t/p/w500${person.profile_path}`}
                alt={person.name}
                className="w-full rounded-lg shadow-lg"
                onError={(e) => {
                  e.target.onerror = null;
                  e.target.src = '/placeholder-person.png';
                }}
              />
            ) : (
              <div className="bg-gray-700 rounded-lg h-96 flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-24 w-24 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
            )}
          </div>

          {/* Person Info */}
          <div className="md:w-2/3 p-6">
            <h1 className="text-4xl font-bold mb-2 text-white">{person.name}</h1>
            
            {person.gender && (
              <div className="flex items-center gap-2 mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
                <span className="text-gray-300 capitalize">{person.gender}</span>
              </div>
            )}
            
            {person.place_of_birth && (
              <div className="flex items-center gap-2 mb-6">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span className="text-gray-300">{person.place_of_birth}</span>
              </div>
            )}

            {person.biography && (
              <div className="mb-8">
                <h2 className="text-2xl font-semibold mb-4 text-white">Biography</h2>
                <p className="text-gray-300 whitespace-pre-line leading-relaxed">
                  {person.biography}
                </p>
              </div>
            )}

            {person.alias?.length > 0 && (
              <div className="mb-8">
                <h3 className="font-semibold text-lg mb-3 text-white">Also Known As</h3>
                <div className="flex flex-wrap gap-2">
                  {person.alias.map((name, index) => (
                    <span key={index} className="bg-gray-700 text-gray-300 px-3 py-1 rounded-full text-sm">
                      {name}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Known For Movies */}
        {movies.length > 0 && (
          <div className="p-6 border-t border-gray-700">
            <h2 className="text-2xl font-bold mb-6 text-white">Known For</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
              {movies.map(movie => (
                <MovieCard key={movie.id} movie={movie} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}