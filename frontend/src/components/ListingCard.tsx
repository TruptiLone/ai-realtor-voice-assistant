import React from 'react';
import { Link } from 'react-router-dom';
import styles from './ListingCard.module.css';

export type ListingCardProps = {
  id: number;
  address: string;
  bedrooms: number;
  bathrooms: number;
  homeSizeSqft: number;
  imageUrl: string;
};

export default function ListingCard({
  id, address, bedrooms, bathrooms, homeSizeSqft, imageUrl
}: ListingCardProps) {
  const fullImageUrl = `${imageUrl}`;

  return (
    <div className={styles.card}>
      <div className={styles.image}>
        <img src={fullImageUrl} alt="House" className={styles.houseImg} />
      </div>

      <div className={styles.info}>
        <h2 className={styles.title}>{address}</h2>
        <p className={styles.details}>
          {bedrooms} bd • {bathrooms} ba • {homeSizeSqft} sqft
        </p>
      </div>

      <div className={styles.buttonWrapper}>
        <Link to={`/listing/${id}`}>
          <button className={styles.selectButton}>Select</button>
        </Link>
      </div>
    </div>
  );
}
