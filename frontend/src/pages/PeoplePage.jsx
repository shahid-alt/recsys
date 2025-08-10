import React, { useState, useEffect } from 'react';
import { fetchPeople } from '../api/tmdb';
import Pagination from '../components/Pagination';
import { Link } from 'react-router-dom';

export default function PeoplePage() {
  const [people, setPeople] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    const getPeople = async () => {
      try {
        setLoading(true);
        const response = await fetchPeople(currentPage);
        setPeople(response.data.results);
        setTotalPages(Math.ceil(response.data.total_count / 20));
      } catch (error) {
        console.error("Error fetching people:", error);
      } finally {
        setLoading(false);
      }
    };

    getPeople();
  }, [currentPage]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-amber-500"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8 text-center text-white">Popular People</h1>
      
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
        {people.map(person => (
          <Link 
            to={`/people/${person.id}`} 
            key={person.id} 
            className="group"
          >
            <div className="bg-gray-800 rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-all duration-300 hover:-translate-y-1 h-full flex flex-col">
              <div className="relative pb-[125%]">
                {person.profile_path ? (
                  <img
                    src={`https://image.tmdb.org/t/p/w300${person.profile_path}`}
                    alt={person.name}
                    className="absolute top-0 left-0 w-full h-full object-cover group-hover:opacity-80 transition-opacity"
                    onError={(e) => {
                      e.target.onerror = null;
                      e.target.src = '/placeholder-person.png';
                    }}
                  />
                ) : (
                  <div className="absolute top-0 left-0 w-full h-full bg-gray-700 flex items-center justify-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-4">
                  <h3 className="font-bold text-white">{person.name}</h3>
                </div>
              </div>
              <div className="p-4 flex-grow">
                <h3 className="font-semibold text-lg text-white">{person.name}</h3>
                {person.place_of_birth && (
                  <p className="text-sm text-gray-400 mt-1">{person.place_of_birth}</p>
                )}
              </div>
            </div>
          </Link>
        ))}
      </div>

      <Pagination 
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={setCurrentPage}
      />
    </div>
  );
}