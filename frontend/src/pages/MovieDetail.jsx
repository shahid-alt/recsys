import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchMovieDetails, fetchMovieCredits } from '../api/tmdb';
import axios from 'axios';

export default function MovieDetail() {
  const { id } = useParams();
  const [movie, setMovie] = useState(null);
  const [credits, setCredits] = useState([]);
  const [castDetails, setCastDetails] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        const [movieResponse, creditsResponse] = await Promise.all([
          fetchMovieDetails(id),
          fetchMovieCredits(id)
        ]);
        
        setMovie(movieResponse.data);
        setCredits(creditsResponse.data);
        
        const uniquePersonIds = [...new Set(creditsResponse.data.map(c => c.person_id))];
        const details = {};
        
        await Promise.all(
          uniquePersonIds.map(async personId => {
            try {
              const response = await axios.get(`http://localhost:8000/people/${personId}/`);
              details[personId] = response.data;
            } catch (error) {
              console.error(`Error fetching person ${personId}:`, error);
              details[personId] = null;
            }
          })
        );
        
        setCastDetails(details);
      } catch (error) {
        console.error("Error fetching movie data:", error);
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
  
  if (!movie) return (
    <div className="text-center p-8 text-gray-300">
      Movie not found
    </div>
  );

  return (
    <div className="container mx-auto px-4 py-8">
      <Link 
        to="/" 
        className="inline-flex items-center gap-2 text-amber-400 hover:text-amber-300 transition-colors mb-6"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
        </svg>
        Back to Home
      </Link>

      {/* Movie Details */}
      <div className="bg-gray-800 rounded-xl shadow-xl overflow-hidden mb-8">
        <div className="md:flex">
          <div className="md:w-1/3">
            <img
              src={movie.poster_path 
                ? `https://image.tmdb.org/t/p/w500${movie.poster_path}`
                : '/placeholder.svg'}
              alt={movie.title}
              className="w-full h-full object-cover"
              onError={(e) => {
                e.target.onerror = null;
                e.target.src = '/placeholder.svg';
              }}
            />
          </div>
          <div className="p-6 md:w-2/3">
            <h1 className="text-3xl font-bold mb-2 text-white">{movie.title}</h1>
            {movie.original_title && movie.original_title !== movie.title && (
              <h2 className="text-xl text-gray-400 mb-4">{movie.original_title}</h2>
            )}
            
            <div className="flex flex-wrap gap-2 mb-6">
              {movie.vote_average > 0 && (
                <span className="bg-amber-500/20 text-amber-400 px-3 py-1 rounded-full flex items-center gap-1">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                  {movie.vote_average.toFixed(1)}
                </span>
              )}
              {movie.runtime > 0 && (
                <span className="bg-gray-700 text-gray-300 px-3 py-1 rounded-full">
                  {movie.runtime} min
                </span>
              )}
              {movie.release_date && (
                <span className="bg-gray-700 text-gray-300 px-3 py-1 rounded-full">
                  {new Date(movie.release_date).getFullYear()}
                </span>
              )}
              {movie.status && (
                <span className="bg-gray-700 text-gray-300 px-3 py-1 rounded-full">
                  {movie.status}
                </span>
              )}
            </div>

            <div className="mb-6">
              <h3 className="text-xl font-semibold mb-2 text-white">Overview</h3>
              <p className="text-gray-300">{movie.overview || 'No overview available'}</p>
            </div>

            {movie.language && (
              <p className="text-gray-400">
                <span className="font-semibold text-gray-300">Original Language:</span> {movie.language}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Cast Section */}
      {credits.length > 0 && (
        <div className="bg-gray-800 rounded-xl shadow-xl overflow-hidden p-6">
          <h2 className="text-2xl font-bold mb-6 text-white">Cast</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6">
            {credits.map(credit => {
              const person = castDetails[credit.person_id];
              return (
                <div key={credit.id} className="text-center group">
                  <Link 
                    to={`/people/${credit.person_id}`} 
                    className="block hover:opacity-90 transition-opacity"
                  >
                    <div className="bg-gray-700 rounded-full w-20 h-20 mx-auto mb-3 overflow-hidden shadow-md group-hover:shadow-amber-400/20 transition-shadow">
                      {person?.profile_path ? (
                        <img
                          src={`https://image.tmdb.org/t/p/w200${person.profile_path}`}
                          alt={credit.name}
                          className="w-full h-full object-cover"
                          loading="lazy"
                          onError={(e) => {
                            e.target.onerror = null;
                            e.target.src = '/placeholder-person.png';
                          }}
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center bg-gray-600">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                          </svg>
                        </div>
                      )}
                    </div>
                    <h3 className="font-medium text-sm text-white">{credit.name}</h3>
                    {credit.character_name && (
                      <p className="text-xs text-gray-400 truncate">as {credit.character_name}</p>
                    )}
                  </Link>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {credits.length === 0 && (
        <div className="bg-gray-800 rounded-xl shadow-xl overflow-hidden p-6 text-center py-8">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-gray-300">Cast information not available</h3>
          <p className="mt-1 text-gray-500">We couldn't find any cast details for this movie</p>
        </div>
      )}
    </div>
  );
}