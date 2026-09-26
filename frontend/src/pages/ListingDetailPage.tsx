import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import styles from './ListingDetailPage.module.css';
import type { ListingCardProps } from '../components/ListingCard';
import FloatingButton from '../components/FloatingButton';
import ChatbotPopup from '../components/ChatBotPopup';

export default function ListingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const listingId = Number(id);

  const [listing, setListing] = useState<ListingCardProps | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);

  useEffect(() => {
    const fetchListing = async () => {
      try {
        const res = await fetch("http://localhost:8000/properties");
        const data = await res.json();
        const matched = data.find((l: ListingCardProps) => l.id === listingId);
        if (matched) {
          setListing(matched);
        } else {
          setError(true);
        }
      } catch (err) {
        console.error("Error fetching listing:", err);
        setError(true);
      } finally {
        setLoading(false);
      }
    };

    fetchListing();
  }, [listingId]);

  const simulateUserMessage = (transcript: string, audio_base64: string) => {
    setMessages(prev => [
      ...prev,
      // Future use: enable text/audio logs if needed
      // { sender: "You", text: transcript },
      // { sender: "Bot", text: "🤖 (reply)", audio: audio_base64 },
    ]);
  };

  if (loading) {
    return <div className={styles.container}><p>Loading...</p></div>;
  }

  if (error || !listing) {
    return (
      <div className={styles.container}>
        <p className={styles.notFound}>Listing not found.</p>
        <Link to="/" className={styles.backLink}>&larr; Back to Listings</Link>
      </div>
    );
  }

  const fullImageUrl = `http://localhost:8000${listing.imageUrl}`;

  return (
    <div className={styles.container}>
      <Link to="/" className={styles.backLink}>&larr; Back to Listings</Link>

      <div className={styles.header}>
        <h1 className={styles.title}>{listing.address}</h1>
      </div>

      <div className={styles.content}>
        <div className={styles.imageWrapper}>
          <img
            src={fullImageUrl}
            alt={`House at ${listing.address}`}
            className={styles.image}
          />
        </div>

        <div className={styles.info}>
          <ul className={styles.specs}>
            <li><strong>Bedrooms:</strong> {listing.bedrooms}</li>
            <li><strong>Bathrooms:</strong> {listing.bathrooms}</li>
            <li><strong>Size:</strong> {listing.homeSizeSqft} sqft</li>
          </ul>

          <Link to={`/tour/${listing.id}`}>
            <button className={styles.tourButton}>Start Tour</button>
          </Link>
        </div>
      </div>

      <>
        <FloatingButton onClick={() => setShowChat(true)} />
        {showChat && (
          <ChatbotPopup
            onClose={() => setShowChat(false)}
            simulateUserMessage={simulateUserMessage}
            setMessages={setMessages}
            propertyId={listingId}
          />
        )}
      </>
    </div>
  );
}
