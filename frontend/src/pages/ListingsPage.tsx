import React, { useState, useEffect } from 'react';
import ListingCard, { ListingCardProps } from '../components/ListingCard';
import styles from './ListingsPage.module.css';

export default function ListingsPage() {
  const [listings, setListings] = useState<ListingCardProps[]>([]);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetch('http://localhost:8000/properties')
      .then(res => res.json())
      .then(data => setListings(data))
      .catch(err => console.error('Failed to fetch listings:', err));
  }, []);

  const filteredListings = listings.filter((l) =>
    l.address.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className={styles.container}>
      <h1 className={styles.header}>AI Home Tours</h1>

      <div className={styles.searchWrapper}>
        <input
          type="text"
          placeholder="Search listings…"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className={styles.searchInput}
        />
      </div>

      <div className={styles.listings}>
        {filteredListings.map((listing) => (
          <ListingCard
            key={listing.id}
            id={listing.id}
            address={listing.address}
            bedrooms={listing.bedrooms}
            bathrooms={listing.bathrooms}
            homeSizeSqft={listing.homeSizeSqft}
            imageUrl={`http://localhost:8000${listing.imageUrl}`}  // 🔥 Update image URL here
          />
        ))}
      </div>
    </div>
  );
}
