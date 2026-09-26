import React, { useState, useRef, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import styles from "./TourPage.module.css";

type Room = {
  name: string;
  imageUrls?: string[];
  audioUrl?: string;
  description: string;
};

type Tour = {
  id: number;
  welcomeAudioUrl?: string;
  rooms: Room[];
};

export default function TourPage() {
  const { id } = useParams<{ id: string }>();
  const [tour, setTour] = useState<Tour | null>(null);
  const [roomIndex, setRoomIndex] = useState(0);
  const [carouselIndex, setCarouselIndex] = useState(0);
  const [menuOpen, setMenuOpen] = useState(false);
  const sidebarRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    fetch(`http://localhost:8000/tour/${id}`)
      .then(res => res.json())
      .then(data => setTour(data))
      .catch(err => {
        console.error("Failed to load tour:", err);
        setTour(null);
      });
  }, [id]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (sidebarRef.current && !sidebarRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    }
    if (menuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [menuOpen]);

  if (!tour || !tour.rooms || tour.rooms.length === 0) {
    return (
      <div className={styles.container}>
        <p>Tour not available for this listing.</p>
        <Link to="/" className={styles.back}>← Back to Listings</Link>
      </div>
    );
  }

  const currentRoom = tour.rooms[roomIndex];

  const goToRoom = (index: number) => {
    setRoomIndex(index);
    setCarouselIndex(0);
    setMenuOpen(false);
  };

  const handleCarouselClick = (direction: 'prev' | 'next') => {
    if (direction === 'prev') {
      setCarouselIndex(prev => Math.max(prev - 1, 0));
    } else {
      setCarouselIndex(prev => Math.min(prev + 1, (currentRoom.imageUrls?.length || 1) - 1));
    }
  };

  return (
    <div className={styles.container}>
      <button
        className={styles.menuButton}
        onClick={() => {
          setMenuOpen(!menuOpen);
        }}
        aria-label="Show room list"
      >
        ☰ Rooms
      </button>

      {menuOpen && (
        <>
          <div className={styles.overlay} />
          <div className={styles.sidebar} ref={sidebarRef}>
            <h2 className={styles.sidebarHeader}>All Rooms</h2>
            <ul className={styles.roomList}>
              {tour.rooms.map((r, i) => (
                <li
                  key={i}
                  className={
                    i === roomIndex
                      ? `${styles.roomItem} ${styles.activeRoom}`
                      : styles.roomItem
                  }
                  onClick={() => goToRoom(i)}
                >
                  {r.name}
                </li>
              ))}
            </ul>
          </div>
        </>
      )}

      <h1 className={styles.header}>{currentRoom.name}</h1>

      {currentRoom.imageUrls && currentRoom.imageUrls.length > 0 && (
        <div className={styles.carouselWrapper}>
          <button
            onClick={() => handleCarouselClick('prev')}
            disabled={carouselIndex === 0}
            className={styles.carouselButton}
          >
            ◀
          </button>
          <img
            src={`http://localhost:8000${currentRoom.imageUrls[carouselIndex]}`}
            alt={`${currentRoom.name} ${carouselIndex + 1}`}
            className={styles.image}
          />
          <button
            onClick={() => handleCarouselClick('next')}
            disabled={carouselIndex === currentRoom.imageUrls.length - 1}
            className={styles.carouselButton}
          >
            ▶
          </button>
        </div>
      )}

      <p className={styles.description}>{currentRoom.description}</p>

      {currentRoom.audioUrl && (
        <audio
          ref={audioRef}
          key={currentRoom.audioUrl}
          controls
          className={styles.audio}
        >
          <source src={`http://localhost:8000${currentRoom.audioUrl}`} type="audio/mp3" />
          Your browser does not support the audio element.
        </audio>
      )}

      <div className={styles.nav}>
        <button 
          onClick={() => goToRoom(roomIndex - 1)} 
          disabled={roomIndex === 0}
        >
          ← Previous
        </button>
        <span>
          Room {roomIndex + 1} of {tour.rooms.length}
        </span>
        <button
          onClick={() => goToRoom(roomIndex + 1)}
          disabled={roomIndex === tour.rooms.length - 1}
        >
          Next →
        </button>
      </div>

      <Link to="/" className={styles.back}>← Back to Listings</Link>
    </div>
  );
}
